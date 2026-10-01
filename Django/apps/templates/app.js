async function initiatePayment(providerName, totalAmount) {
    // Yuboriladigan ma'lumotlar struktura ko'rinishi
    const requestData = {
        provider: providerName, // 'PAYME' yoki 'CLICK'
        amount: totalAmount     // Masalan: 180000
    };

    try {
        // Django API manziliga POST so'rovi yuboramiz
        const response = await fetch('/payment/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getDjangoCSRFToken() // Django xavfsizlik kaliti
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (response.ok && result.pay_url) {
            // Agar backend havola qaytarsa, foydalanuvchini o'sha sahifaga o'tkazamiz
            window.location.href = result.pay_url;
        } else {
            alert("To'lov xatoligi: " + (result.detail || "Tizim sozlamalarini tekshiring."));
        }
    } catch (err) {
        console.error("Tarmoq xatoligi:", err);
        alert("Server bilan aloqa o'rnatib bo'lmadi.");
    }
}

// Django CSRF xavfsizlik tokenni brauzerdan o'qib olish funksiyasi
function getDjangoCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}