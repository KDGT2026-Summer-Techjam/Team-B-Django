document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const publicId = body.dataset.publicId;
    if (!publicId) {
        return;
    }
    // 編集トークンはURLのクエリで受け取り、保存時はX-Edit-Tokenヘッダで送る
    // （URLに載せたまま送らないため）
    const editToken = new URLSearchParams(window.location.search).get(
        "edit_token",
    );

    const btnComplete = document.getElementById("btn-complete");

    const inputTitle = document.getElementById("input-title");
    const inputDate = document.getElementById("input-date");
    const inputTime = document.getElementById("input-time");
    const inputLocation = document.getElementById("input-location");
    const inputAuthor = document.getElementById("input-author");
    const inputMembers = document.getElementById("input-members");

    const editableInputs = [inputTitle, inputDate, inputLocation, inputAuthor];

    // 今日より前の日付を選択できないようにする
    const today = new Date().toISOString().split("T")[0];
    inputDate.setAttribute("min", today);

    // 画像アップロード関連の要素（画像は任意項目のためeditableInputsには含めない）
    // 受け付ける形式・サイズ上限はevents/views_api.pyのPHOTO_DATA_URL_PREFIXES・PHOTO_MAX_LENGTHと合わせる
    const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
    const IMAGE_MAX_LENGTH = 5 * 1024 * 1024;
    const imageSection = document.getElementById("image-section");
    const inputImage = document.getElementById("input-image");
    const imagePreview = document.getElementById("image-preview");
    const imagePlaceholderIcon = document.getElementById("image-placeholder-icon");
    const btnRemoveImage = document.getElementById("btn-remove-image");
    const errorImage = document.getElementById("error-image");
    // 読み込み時の画像、または新たに選択・削除した画像。未変更ならpayloadに含めない
    let selectedImageDataUrl = null;
    let imageChanged = false;

    // 画像エリアのクリックでファイル選択ダイアログを開く
    imageSection.addEventListener("click", () => {
        inputImage.click();
    });

    function showImageError(message) {
        errorImage.textContent = message;
        errorImage.style.display = "block";
        inputImage.value = "";
    }

    function showImagePreview(dataUrl) {
        imagePreview.src = dataUrl;
        imagePreview.style.display = "block";
        imagePlaceholderIcon.style.display = "none";
        btnRemoveImage.style.display = "inline";
    }

    function clearImagePreview() {
        imagePreview.src = "";
        imagePreview.style.display = "none";
        imagePlaceholderIcon.style.display = "block";
        btnRemoveImage.style.display = "none";
    }

    // ファイル選択時に形式・サイズを検証し、Base64へ変換してプレビュー表示する
    inputImage.addEventListener("change", () => {
        const file = inputImage.files[0];
        if (!file) {
            return;
        }

        errorImage.style.display = "none";
        errorImage.textContent = "";

        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
            showImageError("対応していない画像形式です（JPEG/PNG/WEBPのみ）");
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            const dataUrl = reader.result;
            if (dataUrl.length > IMAGE_MAX_LENGTH) {
                showImageError("画像のサイズが大きすぎます（5MB以下にしてください）");
                return;
            }
            selectedImageDataUrl = dataUrl;
            imageChanged = true;
            showImagePreview(selectedImageDataUrl);
        };
        reader.onerror = () => {
            showImageError("画像の読み込みに失敗しました");
        };
        reader.readAsDataURL(file);
    });

    // 画像を削除ボタン：選択中の画像を外す（保存時にimage: nullとして送る）
    btnRemoveImage.addEventListener("click", (event) => {
        event.stopPropagation();
        selectedImageDataUrl = null;
        imageChanged = true;
        inputImage.value = "";
        clearImagePreview();
    });

    // CSRFトークン取得
    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }

        return cookieValue;
    }

    // エラーを消す
    function clearErrors() {
        document.querySelectorAll(".error-msg").forEach((element) => {
            element.textContent = "";
            element.style.display = "none";
        });
    }

    // エラーを表示
    function showError(message) {
        let targetId = "error-title";

        if (message === "日付が不正です" || message === "過去の日時は指定できません") {
            targetId = "error-date";
        } else if (message === "時間が不正です") {
            targetId = "error-time";
        } else if (message === "投稿者名を入力してください") {
            targetId = "error-author";
        } else if (message === "必須項目を入力してください") {
            targetId = "error-title";
        } else if (message === "画像の形式が不正です" || message === "画像のサイズが大きすぎます") {
            targetId = "error-image";
        }

        const target = document.getElementById(targetId);

        target.textContent = message;
        target.style.display = "block";
    }

    // フォームの入力状態を確認
    function validateForm() {
        const isAllFilled = editableInputs.every(
        (input) => input.value.trim() !== "",
        );

        btnComplete.disabled = !isAllFilled;
    }

    // 編集可能な入力欄が変更されたらチェック
    editableInputs.forEach((input) => {
        input.addEventListener("input", validateForm);
        input.addEventListener("change", validateForm);
    });

    // イベント情報を取得
    async function loadEvent() {
        try {
            const response = await fetch(`/api/events/${publicId}`, {
                method: "GET",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
            });

            if (!response.ok) {
                throw new Error("イベント情報の取得に失敗しました");
            }

            const data = await response.json();

            // 編集可能な項目
            inputTitle.value = data.title;
            inputDate.value = data.event_date;
            inputLocation.value = data.location;
            inputAuthor.value = data.organizer_name;

            // 時間：編集可能（任意項目）
            // APIは秒付きISO形式("HH:MM:SS")で返すが、input[type=time]は
            // "HH:MM"でないと未変更のまま再送信した際にサーバー側の検証で弾かれるため切り詰める
            inputTime.value = data.start_time ? data.start_time.slice(0, 5) : "";

            // 画像：編集可能（任意項目）。読み込み時点では未変更として扱う
            selectedImageDataUrl = data.image || null;
            imageChanged = false;
            if (selectedImageDataUrl) {
                showImagePreview(selectedImageDataUrl);
            } else {
                clearImagePreview();
            }

            // メンバー
            if (data.participants && data.participants.length > 0) {
                inputMembers.textContent = data.participants
                .map((participant) => participant.name)
                .join("、");
            } else {
                inputMembers.textContent = "名前";
            }

            validateForm();
        } catch (error) {
            console.error("API Error:", error);
            showError("イベント情報の取得に失敗しました。");
        }
    }

    // 完了ボタン
    btnComplete.addEventListener("click", async () => {
        clearErrors();

        const payload = {
            title: inputTitle.value.trim(),
            event_date: inputDate.value,
            location: inputLocation.value.trim(),
            organizer_name: inputAuthor.value.trim(),
        };

        // 時間は任意項目のため、入力されている場合のみpayloadに含める
        if (inputTime.value) {
            payload.start_time = inputTime.value;
        }

        // 画像は変更した場合のみpayloadに含める（未変更なら送らない。削除時はnullを送る）
        if (imageChanged) {
            payload.image = selectedImageDataUrl;
        }

        try {
            btnComplete.disabled = true;

            const headers = {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            };

            if (editToken) {
                headers["X-Edit-Token"] = editToken;
            }

            const response = await fetch(`/api/events/${publicId}`, {
                method: "PATCH",
                headers: headers,
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                window.location.href = `/e/${publicId}/`;
                return;
            }

            const errorData = await response.json();

            if (errorData.error) {
                showError(errorData.error);
            }

            validateForm();
        } catch (error) {
            console.error("API Error:", error);
            showError("通信エラーが発生しました。");
            validateForm();
        }
    });

    // ページ読み込み時にイベント情報を取得
    loadEvent();
});
