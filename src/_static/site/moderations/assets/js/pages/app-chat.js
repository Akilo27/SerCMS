class Chat {
    constructor() {
        this.chatContainer = null;
        this.simplebar = null;
        this.scrollPosition = 0;
    }

    // Инициализация слайдера
    initStatus() {
        try {
            new Swiper(".mySwiper", {
                loop: false,
                pagination: {
                    el: ".swiper-pagination",
                    clickable: true,
                },
                slidesPerView: "auto",
                spaceBetween: 8,
                autoHeight: true,
            });
        } catch (error) {
            console.error("Ошибка инициализации Swiper:", error);
        }
    }

    // Инициализация чатов
    initChats() {
        const chatContainer = document.querySelector(".chat-conversation-list");
        if (!chatContainer) {
            console.error("Контейнер чатов не найден");
            return;
        }

        this.chatContainer = chatContainer;
        this.simplebar = new SimpleBar(chatContainer);
        this.scrollToBottom(false);

        const form = document.querySelector("form#chat-form");
        if (!form) {
            console.error("Форма чата не найдена");
            return;
        }

        const inputField = form.querySelector("input");
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            const messageContent = inputField.value.trim();
            if (messageContent.length > 0) {
                inputField.value = "";
                this.sendMessage(messageContent);
            }
        });

        const scrollElement = this.simplebar.getScrollElement();
        if (scrollElement) {
            scrollElement.onscroll = (event) => {
                this.scrollPosition = event.target.scrollTop;
            };
        }
    }

    // Отправка сообщения
    sendMessage(content) {
        const messageNode = this.toNodes(this.createHTMLMessageFromMe(content));
        const contentElement = this.simplebar.getContentElement();

        if (contentElement) {
            contentElement.appendChild(messageNode);
            this.simplebar.recalculate();
            this.scrollToBottom();
            setTimeout(() => {
                this.receiveMessage("Server is not connected 😔");
            }, 1000);
        }
    }

    // Получение сообщения
    receiveMessage(content) {
        const messageNode = this.toNodes(this.createHTMLMessageFromOther(content));
        const contentElement = this.simplebar.getContentElement();

        if (contentElement) {
            contentElement.appendChild(messageNode);
            this.simplebar.recalculate();
            this.scrollToBottom();
        }
    }

    // Форматирование времени
    formatTime(date) {
        return new Intl.DateTimeFormat("en-US", {
            hour: "numeric",
            minute: "numeric",
            hour12: true,
        }).format(date);
    }

    // Создание HTML для сообщения от текущего пользователя
    createHTMLMessageFromMe(content) {
        const time = this.formatTime(new Date());
        return `
        <li class="clearfix odd">
            <div class="chat-conversation-text ms-0">
                <div class="d-flex justify-content-end">
                    <div class="chat-conversation-actions dropdown dropstart">
                        <a href="javascript: void(0);" class="pe-1" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class='ri-more-2-fill fs-18'></i>
                        </a>
                        <div class="dropdown-menu">
                            <a class="dropdown-item" href="javascript: void(0);"><i class="bx bx-share fs-18 me-2"></i>Reply</a>
                            <a class="dropdown-item" href="javascript: void(0);"><i class="bx bx-trash fs-18 me-2"></i>Delete</a>
                        </div>
                    </div>
                    <div class="chat-ctext-wrap">
                        <p>${content}</p>
                    </div>
                </div>
                <p class="text-muted fs-12 mb-0 mt-1">${time}<i class="bx bx-check-double ms-1 text-primary"></i></p>
            </div>
        </li>`;
    }

    // Создание HTML для сообщения от другого пользователя
    createHTMLMessageFromOther(content) {
        const time = this.formatTime(new Date());
        return `
        <li class="clearfix">
            <div class="chat-conversation-text">
                <div class="d-flex">
                    <div class="chat-ctext-wrap">
                        <p>${content}</p>
                    </div>
                    <div class="chat-conversation-actions dropdown dropend">
                        <a href="javascript: void(0);" class="ps-1" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class='ri-more-2-fill fs-18'></i>
                        </a>
                        <div class="dropdown-menu">
                            <a class="dropdown-item" href="javascript: void(0);"><i class="bx bx-share fs-18 me-2"></i>Reply</a>
                            <a class="dropdown-item" href="javascript: void(0);"><i class="bx bx-trash fs-18 me-2"></i>Delete</a>
                        </div>
                    </div>
                </div>
                <p class="text-muted fs-12 mb-0 mt-1 ms-2">${time}</p>
            </div>
        </li>`;
    }

    // Преобразование строки в DOM-узлы
    toNodes(htmlString) {
        return new DOMParser().parseFromString(htmlString, "text/html").body.firstChild;
    }

    // Прокрутка вниз
    scrollToBottom(smooth = true) {
        const contentElement = this.simplebar.getContentElement();
        if (contentElement) {
            contentElement.scrollTop = contentElement.scrollHeight;
        }
    }

    // Инициализация чата
    init() {
        this.initStatus();
        this.initChats();
    }
}

// Запуск чата при загрузке страницы
document.addEventListener("DOMContentLoaded", () => {
    const chat = new Chat();
    chat.init();
});
