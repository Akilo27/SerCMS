//Получение csrf-token
window.csrfToken = "{% csrf_token %}";
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('updateCurrencyForm');
    const radioButtons = form.querySelectorAll('input[type="radio"]');

    radioButtons.forEach(function(radio) {
        radio.addEventListener('change', function() {
            submitForm();
        });
    });

    function submitForm() {
        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-CSRFToken': window.csrfToken
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error('Ошибка:', data.message);
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
            });
    }
});
// Задать вопросс
function submitQuestion() {
    var productId = $('#faqs-form').data('product'); // Получить идентификатор продукта
    var question = $('#faqs-form textarea').val(); // Получить текст вопроса

    // Выполнить AJAX-запрос для отправки вопроса
    $.ajax({
        url: window.urls.faqsAdd,
 // URL для добавления нового вопроса
        method: 'POST',
        data: {
            product_id: productId,
            question: question,
            csrfmiddlewaretoken: '{{ csrf_token }}' // Токен CSRF для безопасности
        },
        success: function(response) {
            if (response.success) {
                // Очистить текстовое поле после отправки
                $('#faqs-form textarea').val('');

                // Обновить список вопросов
                $('#faq-list').load(location.href + ' #faq-list');
            }
        }
    });
}

//Фильтр новое старое по алфавиту
document.addEventListener("DOMContentLoaded", function() {

    var filterSelect = document.getElementById("filterSelect");

    function updateURL() {
        var params = new URLSearchParams(window.location.search);

        // Обновляем параметр 'typ' в зависимости от выбора

        // Обновляем параметр 'filter'
        if (filterSelect.value) {
            params.set("filter", filterSelect.value);
        } else {
            params.delete("filter");
        }

        // Обновляем URL
        window.location.search = params.toString();  // Применяем новый URL с объединенными параметрами
    }

    // Отслеживаем изменение значений в выпадающих списках
    filterSelect.addEventListener("change", updateURL);
});

// полоска фильтра по цене
document.addEventListener("DOMContentLoaded", function() {
    var filterAngle = document.getElementById('filter-angle');
    // For Range Sliders
    var inputLeft = document.getElementById("input-left1");
    var inputRight = document.getElementById("input-right1");

    var thumbLeft = document.querySelector(".slider > .thumb.left");
    var thumbRight = document.querySelector(".slider > .thumb.right");
    var range = document.querySelector(".slider > .range");

    var amountLeft = document.getElementById('amount-left1')
    var amountRight = document.getElementById('amount-right1')

    function setLeftValue() {
        var _this = inputLeft,
            min = parseInt(_this.min),
            max = parseInt(_this.max);

        // Убедиться, что left не превышает right
        _this.value = Math.min(parseInt(_this.value), parseInt(inputRight.value));

        var percent = ((_this.value - min) / (max - min)) * 100;

        thumbLeft.style.left = percent + "%";
        range.style.left = percent + "%";
        amountLeft.innerText = Math.round((_this.value));
    }
    setLeftValue();
    function setRightValue() {
        var _this = inputRight,
            min = parseInt(_this.min),
            max = parseInt(_this.max);

        // Убедиться, что right не ниже left
        _this.value = Math.max(parseInt(_this.value), parseInt(inputLeft.value));

        var percent = ((_this.value - min) / (max - min)) * 100;

        thumbRight.style.right = (100 - percent) + "%";
        range.style.right = (100 - percent) + "%";
        amountRight.innerText = Math.round((_this.value));
    }
    setRightValue();

    inputLeft.addEventListener("input", setLeftValue);
    inputRight.addEventListener("input", setRightValue);

    inputLeft.addEventListener("mouseover", function () {
        thumbLeft.classList.add("hover");
    });
    inputLeft.addEventListener("mouseout", function () {
        thumbLeft.classList.remove("hover");
    });
    inputLeft.addEventListener("mousedown", function () {
        thumbLeft.classList.add("active");
    });
    inputLeft.addEventListener("mouseup", function () {
        thumbLeft.classList.remove("active");
    });

    inputRight.addEventListener("mouseover", function () {
        thumbRight.classList.add("hover");
    });
    inputRight.addEventListener("mouseout", function () {
        thumbRight.classList.remove("hover");
    });
    inputRight.addEventListener("mousedown", function () {
        thumbRight.classList.add("active");
    });
    inputRight.addEventListener("mouseup", function () {
        thumbRight.classList.remove("active");
    });
});


//Добавить отзывы
// jQuery для обработки отправки формы и выполнения AJAX-запроса

// Оставить заявку
function submitForm(button) {
    var modalContent = button.closest('.modal-content');
    var product_id = modalContent.getAttribute('data-product');
    var email = modalContent.querySelector('#floatingInput').value;
    var phone = modalContent.querySelector('#phone').value;
    var content = modalContent.querySelector('#floatingTextarea').value;
    var csrfToken = modalContent.querySelector('#csrf_token').value;

    var data = {
        'product_id': product_id,
        'email': email,
        'phone': phone,
        'content': content,
        'csrfmiddlewaretoken': csrfToken
    };

    fetch('/create-application/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(data).toString()
    })
        .then(response => response.json())
        .then(data => {
            var messageElement = modalContent.querySelector('#application-message');
            if (data.status === 'success') {
                messageElement.textContent = data.message;
                messageElement.style.color = 'green';
                messageElement.style.display = 'block';

                setTimeout(() => {
                    var closeButton = modalContent.querySelector('button[data-applications="True"]');
                    if (closeButton) {
                        closeButton.click();
                    }

                    // Обновляем элемент с id 'no_order_{{product.id}}'
                    var noOrderElementId = '#no_order_' + product_id;
                    $(noOrderElementId).load(location.href + ' ' + noOrderElementId);

                }, 2000);

            } else {
                messageElement.textContent = 'Error creating application';
                messageElement.style.color = 'red';
                messageElement.style.display = 'block';
            }
        })
        .catch(error => {
            var messageElement = modalContent.querySelector('#application-message');
            messageElement.textContent = 'An error occurred';
            messageElement.style.color = 'red';
            messageElement.style.display = 'block';
            console.error('Error:', error);
        });
}

// Добавление & Удаление закладок
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');
    bindBookmarkButtonHandler();
});

function getCSRFToken() {
    return window.csrfToken || null;
}

function handleBookmark(event) {
    event.preventDefault(); // Prevent default action if needed
    var button = event.currentTarget;
    var product_id = button.getAttribute('data-product');
    var type = button.getAttribute('data-type');
    var csrfToken = getCSRFToken();


    var url = '';
    if (type === 'bookmarkAdd') {
    url = window.urls.bookmarkAdd;
} else if (type === 'bookmarkDelete') {
    url = window.urls.bookmarkDelete;
}


    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
        },
        body: new URLSearchParams({
            'product_id': product_id,
            'csrfmiddlewaretoken': csrfToken,
        }).toString(),
    })
        .then(response => response.json())
        .then(data => {

            if (data.status === 'success') {
                // Обновление .bookmark-list
                var bookmarkList = document.querySelector('.bookmark-list');
                console.log(data.status)
                console.log(bookmarkList)
                if (bookmarkList) {
                    fetch(location.href)
                        .then(response => response.text())
                        .then(html => {

                            var parser = new DOMParser();
                            var doc = parser.parseFromString(html, 'text/html');
                            var newBookmarkList = doc.querySelector('.bookmark-list');
                            console.log(doc)
                            if (newBookmarkList) {
                                bookmarkList.innerHTML = newBookmarkList.innerHTML;
                                bindBookmarkButtonHandler(); // Повторная привязка обработчиков
                            }
                        })
                        .catch(error => {
                            console.error('Fetch error:', error);
                        });
                }

                // Обновление кнопки закладки
                var bookmarkButtonId = '#bookmark_button_' + product_id;
                var bookmarkButton = document.querySelector(bookmarkButtonId);
                if (bookmarkButton) {
                    fetch(location.href)
                        .then(response => response.text())
                        .then(html => {
                            var parser = new DOMParser();
                            var doc = parser.parseFromString(html, 'text/html');
                            var newBookmarkButton = doc.querySelector(bookmarkButtonId);
                            if (newBookmarkButton) {
                                bookmarkButton.innerHTML = newBookmarkButton.innerHTML;
                                bindBookmarkButtonHandler(); // Повторная привязка обработчиков
                            }
                        })
                        .catch(error => {
                            console.error('Fetch error:', error);
                        });
                }

                const newBookmarkCount = document.getElementById('bookmark-count');
                if (newBookmarkCount) {
                    const BookmarkCount = document.getElementById('bookmark-count');
                    if (BookmarkCount) {
                        BookmarkCount.textContent = data.count;
                    }
                }

            } else {
                console.error('Error:', data.message);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });

}

function bindBookmarkButtonHandler() {
    var buttons = document.querySelectorAll('.bookmark');
    buttons.forEach(button => {
        button.addEventListener('click', handleBookmark);
    });
}

// Инициализация привязок обработчиков событий
bindBookmarkButtonHandler();

// Добавление в корзину
document.addEventListener("DOMContentLoaded", function() {
    // Функция для обработки отправки формы добавления в корзину
    function handleAddToCartFormSubmit(event) {
        event.preventDefault();  // Останавливаем стандартное поведение отправки формы
        event.stopPropagation(); // Останавливаем дальнейшее распространение события

        const form = event.currentTarget;
        const productId = form.dataset.productId;  // Идентификатор продукта
        const quantity = form.querySelector("input[name='quantity']").value;  // Количество
        const variation_slug = form.querySelector("input[name='variation_slug']").value;  // вариация
        const csrfToken = form.querySelector("input[name='csrfmiddlewaretoken']").value;  // CSRF-токен

        const data = new FormData();  // Создаем объект FormData для отправки данных
        data.append("product_id", productId);  // Добавляем идентификатор продукта
        data.append("quantity", quantity);  // Добавляем количество
        data.append("variation_slug", variation_slug);  // Добавляем вариацию
        data.append("csrfmiddlewaretoken", csrfToken);  // Добавляем CSRF-токен

        // Отправляем POST-запрос для добавления товара в корзину
        fetch(form.action, {
            method: "POST",
            body: data
        })
            .then(response => response.json())  // Парсим JSON-ответ
            .then(data => {
                console.log("Ответ сервера:", data);
                if (data.success) {
                    // Показываем кастомный alert
                    showCustomAlert("Товар добавлен в корзину!");

                    // Обновляем содержимое корзины на основе данных с сервера
                    updateAddCartContent(data.cart_html);
                } else {
                    showCustomAlert(data.message);
                    console.error("Не удалось добавить товар в корзину:", data.message);
                }
            })
            .catch(error => {
                console.error("Ошибка при добавлении товара в корзину:", error);
            });
    }

    // Функция для привязки обработчиков событий к формам добавления в корзину
    function bindAddToCartHandler() {
        document.querySelectorAll("form.add-to-cart-form").forEach(function(form) {
            form.removeEventListener("submit", handleAddToCartFormSubmit); // Сначала удаляем, если уже был привязан
            form.addEventListener("submit", handleAddToCartFormSubmit); // Привязываем обработчик
        });
    }

    // Функция для показа кастомного alert
     function showCustomAlert(message) {
        const alertBox = document.getElementById("custom-alert");
        alertBox.textContent = message;  // Устанавливаем текст сообщения
        alertBox.style.display = "block";  // Показываем alert
        setTimeout(() => {
            alertBox.style.opacity = "1";  // Плавно показываем alert
        }, 10);  // Небольшая задержка для запуска анимации

        // Скрываем alert через 2 секунды с плавным исчезновением
        setTimeout(() => {
            alertBox.style.opacity = "0";  // Плавно скрываем alert
            setTimeout(() => {
                alertBox.style.display = "none";  // Полностью скрываем alert после завершения анимации
            }, 500);  // Время плавного исчезновения совпадает с CSS transition
        }, 2000);
    }

    // Изначально привязываем обработчики событий при загрузке страницы
    bindAddToCartHandler();
});

function updateAddCartContent() {
    fetch(location.href)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Обновляем количество товаров в корзине
            const newCartCount = doc.getElementById('cart-count');
            if (newCartCount) {
                const cartCount = document.getElementById('cart-count');
                if (cartCount) {
                    cartCount.textContent = newCartCount.textContent;
                }
            }

            const newCartCountMobile = doc.getElementById('cart-count-mobile');
            if (newCartCountMobile) {
                const cartCountMobile = document.getElementById('cart-count-mobile');
                if (cartCountMobile) {
                    cartCountMobile.textContent = newCartCountMobile.textContent;
                }
            }

            // Обновляем содержимое корзины
            const newCartContent = doc.getElementById('cart_product_canvas');
            if (newCartContent) {
                const cartContent = document.getElementById('cart_product_canvas');
                if (cartContent) {
                    cartContent.innerHTML = newCartContent.innerHTML;
                }
            }

            // Обновляем отображение суммы и "Корзина пуста"
            const newAmount = doc.getElementById('cart-total-amount');
            const cartTotal = document.querySelector('.cart-total');
            const cartEmpty = document.querySelector('.cart-empty');

            if (newAmount && cartTotal && cartEmpty) {
                const amountText = newAmount.textContent.trim();
                const hasItems = amountText !== "0,00" && amountText !== "0" && amountText !== "";

                if (hasItems) {
                    cartTotal.style.display = '';
                    cartEmpty.style.display = 'none';
                    document.getElementById('cart-total-amount').textContent = amountText;
                } else {
                    cartTotal.style.display = 'none';
                    cartEmpty.style.display = '';
                }
            }

            attachDeleteListeners(); // Повторно прикрепляем обработчики событий удаления
            attachQuantityListeners(); // Прикрепляем обработчики изменения количества
        })
        .catch(error => {
            console.error('Error updating cart content:', error);
        });
}

//Удаления в корзине
document.addEventListener('DOMContentLoaded', function() {
    attachDeleteListeners();
});

function attachDeleteListeners() {
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    document.querySelectorAll('.btn[data-type="delete"]').forEach(button => {
        button.addEventListener('click', function() {
            const selectedProductId = button.getAttribute('data-product');
            deleteProduct(selectedProductId, csrfToken);
        });
    });
}

function deleteProduct(selectedProductId, csrfToken) {
console.log('window.urls:', window.urls);
    console.log('window.urls.deleteSelectedProductCart:', window.urls?.deleteSelectedProductCart);

    const url = window.urls?.deleteSelectedProductCart;
    console.log('URL:', url);

    // если url undefined — нужно исправлять!
    if (!url) {
        alert('Ошибка: URL для удаления товара не определён');
        return;
    }
    console.log(selectedProductId)
    console.log(csrfToken)
    fetch(window.urls.deleteSelectedProductCart, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken
    },
    body: new URLSearchParams({
        'selected_product_id': selectedProductId,
        'csrfmiddlewaretoken': csrfToken
    }).toString()
})

        .then(response => {
            console.log('AJAX success response:', response);
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Network response was not ok.');
            }
        })
        .then(data => {
            console.log('AJAX success response:', data);
            if (data.success) {
                updateCartContent();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('AJAX error response:', error);
            alert('An error occurred while trying to remove the product. Please try again.');
        });
}

function updateCartContent() {
    fetch(location.href)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Обновляем содержимое списка продуктов
            const newListContent = doc.getElementById('list-cart-product');
            if (newListContent) {
                document.getElementById('list-cart-product').innerHTML = newListContent.innerHTML;
            }

            // Обновляем содержимое таблицы с итогами
            const newTotalTable = doc.getElementById('cart-total-table');
            if (newTotalTable) {
                document.getElementById('cart-total-table').innerHTML = newTotalTable.innerHTML;
            }

            // Обновляем количество товаров в корзине
            const newCartCount = doc.getElementById('cart-count');
            if (newCartCount) {
                const cartCount = document.getElementById('cart-count');
                if (cartCount) {
                    cartCount.textContent = newCartCount.textContent;
                }
            }

            // Обновляем содержимое корзины
            const newCartContent = doc.getElementById('cart-content');
            if (newCartContent) {
                const cartContent = document.getElementById('cart-content');
                if (cartContent) {
                    cartContent.innerHTML = newCartContent.innerHTML;
                }
            }

            attachDeleteListeners(); // Повторно прикрепляем обработчики событий удаления
            attachQuantityListeners(); // Прикрепляем обработчики изменения количества
        })
        .catch(error => {
            console.error('Error updating cart content:', error);
        });
}

function attachQuantityListeners() {
    document.querySelectorAll('.quantity-wrapper').forEach(wrapper => {
        wrapper.removeEventListener('click', onQuantityChange); // Удаляем старый обработчик, если он был
        wrapper.addEventListener('click', onQuantityChange);
    });
}

// Изменения в корзине
function getCSRFToken() {
    const csrfInput = document.querySelector("input[name='csrfmiddlewaretoken']");
    return csrfInput ? csrfInput.value : '';
}

document.addEventListener("DOMContentLoaded", function() {
    const containers = document.querySelectorAll(".display-flex");

    containers.forEach((container) => {
        if (!container.hasAttribute("data-handler-added")) {
            container.addEventListener("click", onQuantityChange);
            container.setAttribute("data-handler-added", "true");
        }
    });
});

// Обработчик для изменения количества
function onQuantityChange(event) {
    event.stopPropagation();  // Остановить распространение события

    const target = event.target;
    const type = target.getAttribute("data-type");

    if (type !== "plus" && type !== "minus") {
        return;  // Если не "плюс" или "минус", ничего не делаем
    }

    const container = target.closest(".display-flex");
    const quantityInput = container.querySelector("input.qty");
    const productId = container.getAttribute("data-product");
    const price = parseFloat(container.getAttribute("data-price"));
    let currentQuantity = parseInt(quantityInput.value, 10);

    if (isNaN(currentQuantity)) {
        console.error("Invalid quantity");
        return;  // Если значение не число, ничего не делаем
    }

    const maxLength = parseInt(quantityInput.getAttribute("maxlength"), 10);

    let change = 0;  // Величина изменения общей суммы корзины
    if (type === "plus" && currentQuantity < maxLength) {
        currentQuantity += 1;
        change = price;  // Добавляем стоимость продукта
    } else if (type === "minus" && currentQuantity > 1) {
        currentQuantity -= 1;
        change = -price;  // Вычитаем стоимость продукта
    }

    quantityInput.value = currentQuantity;  // Обновляем количество в поле ввода

    const newAmount = currentQuantity * price;  // Вычисляем новый `amount`

    // Обновляем элемент <span data-inter-amount="true">
    const spanToUpdate = document.querySelector(`span[data-product='${productId}'][data-inter-amount='true']`);
    if (spanToUpdate) {
        spanToUpdate.textContent = newAmount.toFixed(2);  // Обновляем значение
    }

    // Обновляем общий `amount` корзины
    const totalAmountSpan = document.querySelector("span#amount");  // Элемент для общей суммы корзины
    if (totalAmountSpan) {
        let currentTotal = parseFloat(totalAmountSpan.textContent);  // Текущий общий `amount`
        if (!isNaN(currentTotal)) {
            totalAmountSpan.textContent = (currentTotal + change).toFixed(2);  // Обновляем общую сумму корзины
        }
    }

    // Отправляем AJAX-запрос на сервер
    fetch(`${productId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ quantity: currentQuantity, amount: newAmount }),  // Передаем данные
    })

}



document.getElementById('commentForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var formData = new FormData(this);

    console.log("Форма отправляется");

    fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        credentials: 'same-origin'
    }).then(response => {
        if (response.ok) {
            return response.json();
        }
        return response.json().then(data => {
            throw new Error(JSON.stringify(data.errors));
        });
    }).then(data => {
        console.log('Успешно отправлено:', data);
        this.reset();
        refreshTicketList();
    }).catch(error => {
        console.error('Ошибка:', error);
    });
});

function refreshTicketList() {
    $('#list-ticket').load(location.href + ' #list-ticket>*', function(response, status, xhr) {
        if (status === "error") {
            console.log("Ошибка при обновлении:", xhr.statusText);
        } else {
            console.log("Список обновлен");
        }
    });
}
