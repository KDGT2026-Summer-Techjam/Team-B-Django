document.addEventListener("DOMContentLoaded", () => {
    const publicId = EVENT_PUBLIC_ID;
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

        if (message === "日付が不正です") {
            targetId = "error-date";
        } else if (message === "投稿者名を入力してください") {
            targetId = "error-author";
        } else if (message === "必須項目を入力してください") {
            targetId = "error-title";
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

            // 表示のみの項目
            // 現在のAPIには時間がないため空欄のまま
            inputTime.value = "";

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
