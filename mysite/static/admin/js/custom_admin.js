/**
 * Custom Admin UX enhancements for TM "Sibsyr"
 * Positions Search and Filters into a unified horizontal top control bar above the table.
 * Transforms filter accordions into clean dropdown menus with outside click dismissal.
 */
document.addEventListener("DOMContentLoaded", function () {
    // 1. Unify Search and Filters into a single horizontal top bar
    const changelistFilter = document.getElementById("changelist-filter");
    const toolbar = document.getElementById("toolbar");
    const changelistForm = document.getElementById("changelist-form");

    if (changelistFilter || toolbar) {
        let topBar = document.getElementById("changelist-top-controls");
        if (!topBar) {
            topBar = document.createElement("div");
            topBar.id = "changelist-top-controls";
            topBar.className = "changelist-top-controls";

            const parent = (toolbar && toolbar.parentNode) || (changelistForm && changelistForm.parentNode);
            const refElement = toolbar || changelistForm;

            if (parent && refElement) {
                parent.insertBefore(topBar, refElement);
                if (toolbar) {
                    topBar.appendChild(toolbar);
                }
                if (changelistFilter) {
                    topBar.appendChild(changelistFilter);
                }
            }
        }
    }

    // 2. Setup horizontal changelist filter dropdowns
    if (changelistFilter) {
        const filterDetails = changelistFilter.querySelectorAll("details");

        filterDetails.forEach(function (detail) {
            // Check if active (selected item is not the first "Все" / "Любая дата" item)
            const selectedLi = detail.querySelector("ul li.selected");
            const firstLi = detail.querySelector("ul li:first-child");

            if (selectedLi && selectedLi !== firstLi) {
                detail.classList.add("has-active-filter");
                const summary = detail.querySelector("summary");
                if (summary) {
                    const originalText = summary.textContent.trim();
                    const activeVal = selectedLi.textContent.trim();
                    summary.innerHTML = `<span style="opacity: 0.85;">${originalText}:</span> <strong style="color: var(--admin-primary);">${activeVal}</strong>`;
                }
            }

            // Close details by default so they behave as clean dropdowns
            detail.removeAttribute("open");
        });

        // Close on click outside
        document.addEventListener("click", function (e) {
            if (!e.target.closest("#changelist-filter details")) {
                filterDetails.forEach(function (d) {
                    d.removeAttribute("open");
                });
            } else {
                // If clicking one details, close all other details
                const current = e.target.closest("#changelist-filter details");
                filterDetails.forEach(function (d) {
                    if (d !== current) {
                        d.removeAttribute("open");
                    }
                });
            }
        });
    }

    // 3. Dynamic Dark/Light Theme adaptation for TinyMCE
    const themeAttr = document.documentElement.getAttribute("data-theme");
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = themeAttr === "dark" || ((themeAttr === "auto" || !themeAttr) && prefersDark);

    document.querySelectorAll(".tinymce").forEach(function (el) {
        if (el.dataset && el.dataset.mceConf) {
            try {
                const conf = JSON.parse(el.dataset.mceConf);
                if (isDark) {
                    conf.skin = "oxide-dark";
                    conf.content_css = "dark";
                } else {
                    conf.skin = "oxide";
                    conf.content_css = "default";
                }
                el.dataset.mceConf = JSON.stringify(conf);
            } catch (e) {}
        }
    });

    // 4. Intelligent SEO Assistant & Generator for Product, Category, and Article change forms
    const metaTitleInput = document.getElementById("id_meta_title");
    const metaDescInput = document.getElementById("id_meta_description");
    const metaKeywordsInput = document.getElementById("id_meta_keywords");

    if (metaTitleInput || metaDescInput) {
        // Setup character counters
        function setupCounter(input, recommendedMin, recommendedMax, label) {
            if (!input) return;
            const container = input.closest(".form-row") || input.parentNode;
            if (!container) return;

            const badge = document.createElement("div");
            badge.className = "seo-char-counter-badge";
            badge.style.cssText = "font-size: 11px; margin-top: 4px; display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 4px; font-weight: 600; transition: all 0.2s ease;";
            container.appendChild(badge);

            function update() {
                const len = (input.value || "").trim().length;
                let statusText = "";
                let bg = "#f1f5f9";
                let text = "#475569";

                if (len === 0) {
                    statusText = "Пусто (применится авто-генерация)";
                    bg = "#fef3c7";
                    text = "#b45309";
                } else if (len >= recommendedMin && len <= recommendedMax) {
                    statusText = `Идеально (${recommendedMin}-${recommendedMax} симв.)`;
                    bg = "#dcfce7";
                    text = "#166534";
                } else if (len > recommendedMax) {
                    statusText = `Длинный (${len} симв., поисковик может обрезать)`;
                    bg = "#fee2e2";
                    text = "#991b1b";
                } else {
                    statusText = `Короткий (${len} симв.)`;
                    bg = "#fef3c7";
                    text = "#92400e";
                }
                badge.style.backgroundColor = bg;
                badge.style.color = text;
                badge.innerHTML = `<i class="bi bi-fonts"></i> ${label}: <strong>${len}</strong> симв. — ${statusText}`;
            }

            input.addEventListener("input", update);
            update();
        }

        setupCounter(metaTitleInput, 45, 70, "Title");
        setupCounter(metaDescInput, 130, 180, "Description");

        // Add "⚡ Сгенерировать SEO" button next to meta_title or at top of SEO fieldset
        const seoRow = (metaTitleInput && metaTitleInput.closest(".form-row")) || (metaDescInput && metaDescInput.closest(".form-row"));
        if (seoRow) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "btn-generate-seo-inline";
            btn.innerHTML = '<i class="bi bi-magic" style="margin-right: 5px;"></i>⚡ Сгенерировать SEO-теги';
            btn.style.cssText = "margin-bottom: 10px; display: inline-flex; align-items: center; background: linear-gradient(135deg, #ff8400 0%, #ea580c 100%); color: #ffffff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer; box-shadow: 0 2px 6px rgba(255, 132, 0, 0.3); transition: all 0.15s ease;";
            
            btn.addEventListener("mouseenter", () => btn.style.transform = "translateY(-1px)");
            btn.addEventListener("mouseleave", () => btn.style.transform = "none");

            btn.addEventListener("click", function() {
                // Determine model type
                const titleInput = document.getElementById("id_title") || document.getElementById("id_name");
                const titleVal = titleInput ? titleInput.value.trim() : "";

                if (!titleVal) {
                    alert("Пожалуйста, сначала укажите название объекта.");
                    return;
                }

                const catSelect = document.getElementById("id_category");
                const catText = (catSelect && catSelect.selectedIndex > 0) ? catSelect.options[catSelect.selectedIndex].text.trim() : "";
                const weightVal = (document.getElementById("id_unit_weight") ? document.getElementById("id_unit_weight").value.trim() : "");
                const pkgVal = (document.getElementById("id_package_type") ? document.getElementById("id_package_type").value.trim() : "");
                const priceVal = (document.getElementById("id_price_numeric") ? document.getElementById("id_price_numeric").value.trim() : "");
                const snippetVal = (document.getElementById("id_snippet") ? document.getElementById("id_snippet").value.trim() : "");

                let newTitle = "";
                let newDesc = "";
                let newKeywords = "";

                if (catSelect !== null) {
                    // Product Form
                    const weightPart = weightVal ? ` ${weightVal}` : "";
                    newTitle = `Купить ${titleVal}${weightPart} от производителя в Омске — ТМ «Сибсыр»`;
                    
                    const catPart = catText ? `категории «${catText}» ` : "";
                    const pricePart = priceVal ? ` Цена от ${priceVal} ₽.` : "";
                    newDesc = `Натуральный сыр ${titleVal}${weightPart} ${catPart}собственного производства ТМ «Сибсыр» в Омске.${pricePart} Доставка по Омску и регионам, оптовые и розничные поставки.`;
                    
                    newKeywords = `${titleVal.toLowerCase()}, ${titleVal.toLowerCase()} омск, сыр омск, купить сыр омск, сибсыр, сулугуни, производитель сыра`;
                    if (catText) {
                        newKeywords += `, ${catText.toLowerCase()}`;
                    }
                } else if (snippetVal !== "") {
                    // Article Form
                    newTitle = `${titleVal} — База знаний и статьи о сыре | ТМ «Сибсыр»`;
                    newDesc = snippetVal.length > 170 ? snippetVal.substring(0, 167) + "..." : snippetVal;
                    newKeywords = `${titleVal.toLowerCase()}, статьи о сыре, сибсыр омск, производство сыра, технологии сыроделия`;
                } else {
                    // Category Form
                    newTitle = `${titleVal} — купить оптом и в розницу от производителя в Омске | ТМ «Сибсыр»`;
                    newDesc = `Полный ассортимент категории «${titleVal}» от завода «Сибсыр» в Омске. Натуральное сырье, 100% ГОСТ, оптовые скидки, поставки спецтранспортом.`;
                    newKeywords = `${titleVal.toLowerCase()}, ${titleVal.toLowerCase()} омск, сыры омск, купить сыр оптом, сибсыр омск, каталог продукции`;
                }

                if (metaTitleInput) {
                    metaTitleInput.value = newTitle;
                    metaTitleInput.dispatchEvent(new Event("input"));
                }
                if (metaDescInput) {
                    metaDescInput.value = newDesc;
                    metaDescInput.dispatchEvent(new Event("input"));
                }
                if (metaKeywordsInput) {
                    metaKeywordsInput.value = newKeywords;
                }

                btn.innerHTML = '<i class="bi bi-check-circle-fill" style="margin-right: 5px;"></i>✓ SEO-теги сгенерированы!';
                btn.style.background = "#10b981";
                setTimeout(() => {
                    btn.innerHTML = '<i class="bi bi-magic" style="margin-right: 5px;"></i>⚡ Сгенерировать SEO-теги';
                    btn.style.background = "linear-gradient(135deg, #ff8400 0%, #ea580c 100%)";
                }, 2500);
            });

            seoRow.parentNode.insertBefore(btn, seoRow);
        }
    }

    // =========================================================================
    // 5. Global Admin Navigation & Dropdowns (Desktop & Mobile)
    // =========================================================================
    const navDropdowns = document.querySelectorAll(".admin-nav-dropdown");

    navDropdowns.forEach(function (dropdown) {
        const btn = dropdown.querySelector(".admin-nav-dropdown-btn");
        if (!btn) return;

        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            const isOpen = dropdown.classList.contains("is-open");

            // Close all other dropdowns
            navDropdowns.forEach(function (d) {
                if (d !== dropdown) {
                    d.classList.remove("is-open");
                    const otherBtn = d.querySelector(".admin-nav-dropdown-btn");
                    if (otherBtn) otherBtn.setAttribute("aria-expanded", "false");
                }
            });

            if (isOpen) {
                dropdown.classList.remove("is-open");
                btn.setAttribute("aria-expanded", "false");
            } else {
                dropdown.classList.add("is-open");
                btn.setAttribute("aria-expanded", "true");
            }
        });
    });

    // Close nav dropdowns on outside click
    document.addEventListener("click", function (e) {
        if (!e.target.closest(".admin-nav-dropdown")) {
            navDropdowns.forEach(function (d) {
                d.classList.remove("is-open");
                const btn = d.querySelector(".admin-nav-dropdown-btn");
                if (btn) btn.setAttribute("aria-expanded", "false");
            });
        }
    });

    // Close on Escape key
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            navDropdowns.forEach(function (d) {
                d.classList.remove("is-open");
                const btn = d.querySelector(".admin-nav-dropdown-btn");
                if (btn) btn.setAttribute("aria-expanded", "false");
            });
        }
    });

    // =========================================================================
    // 6. Mobile Offcanvas Navigation Drawer
    // =========================================================================
    const mobileToggle = document.getElementById("adminMobileMenuToggle");
    const mobileDrawer = document.getElementById("adminMobileDrawer");
    const mobileBackdrop = document.getElementById("adminMobileDrawerBackdrop");
    const mobileClose = document.getElementById("adminMobileDrawerClose");
    const drawerSearch = document.getElementById("adminDrawerSearchInput");

    function openMobileDrawer() {
        if (mobileDrawer && mobileBackdrop) {
            mobileDrawer.classList.add("open");
            mobileBackdrop.classList.add("open");
            document.body.style.overflow = "hidden";
            if (mobileToggle) mobileToggle.setAttribute("aria-expanded", "true");
            if (drawerSearch) drawerSearch.focus();
        }
    }

    function closeMobileDrawer() {
        if (mobileDrawer && mobileBackdrop) {
            mobileDrawer.classList.remove("open");
            mobileBackdrop.classList.remove("open");
            document.body.style.overflow = "";
            if (mobileToggle) mobileToggle.setAttribute("aria-expanded", "false");
        }
    }

    if (mobileToggle) mobileToggle.addEventListener("click", openMobileDrawer);
    if (mobileClose) mobileClose.addEventListener("click", closeMobileDrawer);
    if (mobileBackdrop) mobileBackdrop.addEventListener("click", closeMobileDrawer);

    if (drawerSearch && mobileDrawer) {
        drawerSearch.addEventListener("input", function () {
            const query = this.value.toLowerCase().trim();
            const links = mobileDrawer.querySelectorAll(".admin-drawer-links a, .admin-drawer-single-link");
            links.forEach(function (link) {
                const text = link.textContent.toLowerCase();
                if (text.includes(query)) {
                    link.style.display = "flex";
                } else {
                    link.style.display = "none";
                }
            });
        });
    }

    // =========================================================================
    // 7. Command Palette Modal (Ctrl + K / Quick Nav Search)
    // =========================================================================
    const cmdPalette = document.getElementById("adminCmdPalette");
    const cmdBackdrop = document.getElementById("adminCmdPaletteBackdrop");
    const cmdInput = document.getElementById("adminCmdInput");
    const cmdResults = document.getElementById("adminCmdResults");
    const cmdCloseBtn = document.getElementById("adminCmdCloseBtn");
    const quickSearchBtn = document.getElementById("adminQuickNavSearchBtn");

    // All available routes in TM "Sibsyr" Admin
    const adminRoutes = [
        { title: "Дашборд и сводная аналитика", group: "Главная", url: "/admin/", icon: "bi-speedometer2" },
        { title: "Заказы клиентов (Розничные и B2B)", group: "Продажи", url: "/admin/shop/order/", icon: "bi-cart-check-fill" },
        { title: "Создать новый заказ", group: "Продажи", url: "/admin/shop/order/add/", icon: "bi-cart-plus-fill" },
        { title: "Оптовые заявки (Прайс-листы)", group: "Продажи", url: "/admin/main/wholesalepricerequest/", icon: "bi-file-earmark-spreadsheet-fill" },
        { title: "Оптовая email-рассылка", group: "Продажи", url: "/admin/main/wholesalepricerequest/mailing/", icon: "bi-send-fill" },
        { title: "Скачать оптовый прайс (XLSX)", group: "Продажи", url: "/admin/main/wholesalepricerequest/download/", icon: "bi-file-earmark-excel-fill" },
        { title: "Каталог сыров и товаров", group: "Каталог", url: "/admin/shop/product/", icon: "bi-basket2-fill" },
        { title: "Добавить новый товар", group: "Каталог", url: "/admin/shop/product/add/", icon: "bi-plus-circle-fill" },
        { title: "Категории сырной продукции", group: "Каталог", url: "/admin/shop/category/", icon: "bi-tags-fill" },
        { title: "Акции, скидки и таймеры", group: "Каталог", url: "/admin/shop/promotion/", icon: "bi-percent" },
        { title: "Промокоды и купоны", group: "Каталог", url: "/admin/shop/promocode/", icon: "bi-ticket-perforated-fill" },
        { title: "Отзывы покупателей", group: "Каталог", url: "/admin/shop/review/", icon: "bi-chat-heart-fill" },
        { title: "Профили клиентов (Физ. и Юр. лица)", group: "Клиенты", url: "/admin/accounts/userprofile/", icon: "bi-person-vcard-fill" },
        { title: "Сводная аналитика клиентов", group: "Клиенты", url: "/admin/accounts/", icon: "bi-graph-up-arrow" },
        { title: "Пользователи и операторы", group: "Клиенты", url: "/admin/auth/user/", icon: "bi-person-badge-fill" },
        { title: "Группы прав доступа", group: "Клиенты", url: "/admin/auth/group/", icon: "bi-shield-lock-fill" },
        { title: "Заявки на звонки и связь", group: "Контент", url: "/admin/main/callbackrequest/", icon: "bi-telephone-inbound-fill" },
        { title: "Статьи и публикации блога", group: "Контент", url: "/admin/articles/article/", icon: "bi-journal-bookmark-fill" },
        { title: "FAQ (Вопросы и ответы)", group: "Контент", url: "/admin/main/faqitem/", icon: "bi-question-circle-fill" },
        { title: "Преимущества производства", group: "Контент", url: "/admin/main/productionfeature/", icon: "bi-shield-check" },
        { title: "История развития завода", group: "Контент", url: "/admin/main/companytimeline/", icon: "bi-hourglass-split" },
        { title: "Сертификаты качества ГОСТ", group: "Контент", url: "/admin/main/qualitycertificate/", icon: "bi-award-fill" },
        { title: "Способы доставки продукции", group: "Контент", url: "/admin/main/deliverymethod/", icon: "bi-truck" },
        { title: "Способы оплаты", group: "Контент", url: "/admin/main/paymentmethod/", icon: "bi-credit-card-2-front-fill" },
        { title: "Отделы и контакты служб", group: "Контент", url: "/admin/main/contactdepartment/", icon: "bi-buildings-fill" },
        { title: "Социальные сети и мессенджеры", group: "Контент", url: "/admin/main/sociallink/", icon: "bi-share-fill" },
        { title: "Основные настройки и реквизиты", group: "Настройки", url: "/admin/main/sitesettings/1/change/", icon: "bi-gear-fill" },
        { title: "Витрина интернет-магазина", group: "Сайт", url: "/", icon: "bi-box-arrow-up-right" },
        { title: "Файл robots.txt", group: "Сайт", url: "/robots.txt", icon: "bi-robot" },
        { title: "Карта сайта sitemap.xml", group: "Сайт", url: "/sitemap.xml", icon: "bi-diagram-3-fill" }
    ];

    let selectedIndex = 0;
    let filteredRoutes = [];

    function renderCmdResults(results) {
        if (!cmdResults) return;
        filteredRoutes = results;
        selectedIndex = 0;

        if (results.length === 0) {
            cmdResults.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--admin-text-muted); font-size: 0.9rem;">Ничего не найдено. Попробуйте другой запрос.</div>';
            return;
        }

        cmdResults.innerHTML = results.map((item, idx) => `
            <a href="${item.url}" class="admin-cmd-item ${idx === 0 ? 'selected' : ''}" data-index="${idx}">
                <div class="admin-cmd-item-left">
                    <div class="admin-cmd-item-icon">
                        <i class="bi ${item.icon}"></i>
                    </div>
                    <div class="admin-cmd-item-text">
                        <span class="admin-cmd-item-title">${item.title}</span>
                        <span class="admin-cmd-item-group">${item.group} &bull; ${item.url}</span>
                    </div>
                </div>
                <span class="admin-cmd-item-badge">Перейти &rarr;</span>
            </a>
        `).join("");
    }

    function openCmdPalette() {
        if (cmdPalette && cmdBackdrop) {
            cmdPalette.classList.add("open");
            cmdBackdrop.classList.add("open");
            if (cmdInput) {
                cmdInput.value = "";
                renderCmdResults(adminRoutes);
                setTimeout(() => cmdInput.focus(), 50);
            }
        }
    }

    function closeCmdPalette() {
        if (cmdPalette && cmdBackdrop) {
            cmdPalette.classList.remove("open");
            cmdBackdrop.classList.remove("open");
        }
    }

    if (quickSearchBtn) quickSearchBtn.addEventListener("click", openCmdPalette);
    if (cmdCloseBtn) cmdCloseBtn.addEventListener("click", closeCmdPalette);
    if (cmdBackdrop) cmdBackdrop.addEventListener("click", closeCmdPalette);

    // Global shortcut Ctrl + K or Cmd + K
    document.addEventListener("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            if (cmdPalette && cmdPalette.classList.contains("open")) {
                closeCmdPalette();
            } else {
                openCmdPalette();
            }
        }
        if (e.key === "Escape") {
            closeCmdPalette();
            closeMobileDrawer();
        }
    });

    if (cmdInput) {
        cmdInput.addEventListener("input", function () {
            const query = this.value.toLowerCase().trim();
            if (!query) {
                renderCmdResults(adminRoutes);
                return;
            }
            const filtered = adminRoutes.filter(item => 
                item.title.toLowerCase().includes(query) || 
                item.group.toLowerCase().includes(query) || 
                item.url.toLowerCase().includes(query)
            );
            renderCmdResults(filtered);
        });

        cmdInput.addEventListener("keydown", function (e) {
            const items = cmdResults ? cmdResults.querySelectorAll(".admin-cmd-item") : [];
            if (!items.length) return;

            if (e.key === "ArrowDown") {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % items.length;
                updateSelection(items);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                updateSelection(items);
            } else if (e.key === "Enter") {
                e.preventDefault();
                if (filteredRoutes[selectedIndex]) {
                    window.location.href = filteredRoutes[selectedIndex].url;
                }
            }
        });
    }

    function updateSelection(items) {
        items.forEach((item, idx) => {
            if (idx === selectedIndex) {
                item.classList.add("selected");
                item.scrollIntoView({ block: "nearest" });
            } else {
                item.classList.remove("selected");
            }
        });
    }

    // =========================================================================
    // 8. Live Filter for Section 7 Models on Dashboard
    // =========================================================================
    const modelFilterInput = document.getElementById("sibModelFilterInput");
    const appsGrid = document.getElementById("sibAppsGrid");

    if (modelFilterInput && appsGrid) {
        modelFilterInput.addEventListener("input", function () {
            const q = this.value.toLowerCase().trim();
            const cards = appsGrid.querySelectorAll(".sib-app-card");

            cards.forEach(function (card) {
                const rows = card.querySelectorAll(".sib-app-model-row");
                let visibleCount = 0;

                rows.forEach(function (row) {
                    const text = (row.dataset.model || "" + " " + row.textContent).toLowerCase();
                    if (!q || text.includes(q)) {
                        row.classList.remove("sib-model-hidden");
                        visibleCount++;
                    } else {
                        row.classList.add("sib-model-hidden");
                    }
                });

                if (visibleCount > 0) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        });
    }

    // =========================================================================
    // 9. Interactive Changelist: Drag and Drop for Columns and Rows
    // =========================================================================
    initAdminTableDragAndDrop();
});

/**
 * Toast Notifications for Admin UI
 */
function showAdminToast(type, message) {
    let container = document.getElementById("admin-toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "admin-toast-container";
        container.className = "admin-toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `admin-toast admin-toast-${type}`;
    const icon = type === "success" ? "bi-check-circle-fill" : type === "error" ? "bi-exclamation-triangle-fill" : "bi-info-circle-fill";
    toast.innerHTML = `<i class="bi ${icon}"></i><span>${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("show"));
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

function getAdminCsrfToken() {
    let token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!token) {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        if (match) token = match[1];
    }
    return token || "";
}

function getColumnKey(th) {
    if (!th) return "";
    if (th.classList.contains("action-checkbox-column")) return "action-checkbox-column";
    for (let c of th.classList) {
        if (c.startsWith("column-")) return c;
    }
    return th.textContent.trim().replace(/\s+/g, "_");
}

function initAdminTableDragAndDrop() {
    const table = document.getElementById("result_list");
    if (!table) return;

    const pathname = window.location.pathname;
    const localStorageKey = "admin_table_col_order_" + pathname;

    // -------------------------------------------------------------------------
    // A. Restore Saved Column Order from localStorage
    // -------------------------------------------------------------------------
    const theadTr = table.querySelector("thead tr");
    if (theadTr) {
        let savedCols = null;
        try {
            savedCols = JSON.parse(localStorage.getItem(localStorageKey) || "null");
        } catch (e) {}

        if (Array.isArray(savedCols) && savedCols.length > 0) {
            const allRows = table.querySelectorAll("thead tr, tbody tr, tfoot tr");
            savedCols.forEach(function (colKey) {
                const headers = Array.from(theadTr.children);
                const idx = headers.findIndex(th => getColumnKey(th) === colKey);
                if (idx !== -1) {
                    allRows.forEach(function (row) {
                        const cells = Array.from(row.children);
                        if (cells[idx]) {
                            row.appendChild(cells[idx]);
                        }
                    });
                }
            });
        }
    }

    // Reset column order button in changelist tools
    const topBar = document.getElementById("changelist-top-controls") ||
                   document.getElementById("toolbar") ||
                   document.getElementById("changelist-form");
    if (topBar && !document.getElementById("btnResetColOrder")) {
        const resetBtn = document.createElement("button");
        resetBtn.type = "button";
        resetBtn.id = "btnResetColOrder";
        resetBtn.className = "btn-reset-col-order";
        resetBtn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Сбросить колонки';
        resetBtn.title = "Восстановить исходный порядок столбцов таблицы";
        if (!localStorage.getItem(localStorageKey)) {
            resetBtn.style.display = "none";
        }
        resetBtn.addEventListener("click", function () {
            localStorage.removeItem(localStorageKey);
            showAdminToast("info", "Порядок колонок сброшен");
            setTimeout(() => window.location.reload(), 300);
        });

        // Insert into top bar or toolbar
        if (document.getElementById("changelist-top-controls")) {
            document.getElementById("changelist-top-controls").appendChild(resetBtn);
        } else if (document.getElementById("toolbar")) {
            document.getElementById("toolbar").appendChild(resetBtn);
        } else {
            topBar.insertBefore(resetBtn, topBar.firstChild);
        }
    }

    // -------------------------------------------------------------------------
    // B. Column Drag and Drop
    // -------------------------------------------------------------------------
    let draggedTh = null;
    let draggedColIndex = -1;

    const thElements = Array.from(table.querySelectorAll("thead th"));
    thElements.forEach(function (th) {
        // Pinned action checkbox column (column 0) stays fixed
        if (th.classList.contains("action-checkbox-column")) return;

        // Add grip handle
        if (!th.querySelector(".admin-col-drag-handle")) {
            const handle = document.createElement("span");
            handle.className = "admin-col-drag-handle";
            handle.title = "Перетащите, чтобы изменить порядок столбца";
            handle.innerHTML = '<i class="bi bi-grip-horizontal"></i>';
            handle.setAttribute("draggable", "true");

            const textContainer = th.querySelector(".text") || th;
            textContainer.insertBefore(handle, textContainer.firstChild);

            handle.addEventListener("dragstart", function (e) {
                draggedTh = th;
                draggedColIndex = Array.from(th.parentNode.children).indexOf(th);
                th.classList.add("col-dragging");
                e.dataTransfer.effectAllowed = "move";
                e.dataTransfer.setData("text/plain", getColumnKey(th));
                e.stopPropagation();
            });
        }

        th.setAttribute("draggable", "true");

        th.addEventListener("dragstart", function (e) {
            // Cancel drag if clicked on link or input
            if (e.target.closest("a") || e.target.closest("input") || e.target.closest("button")) {
                e.preventDefault();
                return;
            }
            draggedTh = th;
            draggedColIndex = Array.from(th.parentNode.children).indexOf(th);
            th.classList.add("col-dragging");
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", getColumnKey(th));
        });

        th.addEventListener("dragover", function (e) {
            if (!draggedTh || draggedTh === th) return;
            if (th.classList.contains("action-checkbox-column")) return;
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";

            const rect = th.getBoundingClientRect();
            const isRight = (e.clientX - rect.left) > (rect.width / 2);
            th.classList.remove("col-drop-left", "col-drop-right");
            th.classList.add(isRight ? "col-drop-right" : "col-drop-left");
        });

        th.addEventListener("dragleave", function () {
            th.classList.remove("col-drop-left", "col-drop-right");
        });

        th.addEventListener("drop", function (e) {
            if (!draggedTh || draggedTh === th) return;
            e.preventDefault();
            const isRight = th.classList.contains("col-drop-right");
            th.classList.remove("col-drop-left", "col-drop-right");

            const targetIndex = Array.from(th.parentNode.children).indexOf(th);
            if (draggedColIndex === -1 || targetIndex === -1 || draggedColIndex === targetIndex) return;

            const allRows = table.querySelectorAll("thead tr, tbody tr, tfoot tr");
            allRows.forEach(function (row) {
                const cells = Array.from(row.children);
                const movingCell = cells[draggedColIndex];
                const targetCell = cells[targetIndex];
                if (movingCell && targetCell) {
                    if (isRight) {
                        targetCell.after(movingCell);
                    } else {
                        targetCell.before(movingCell);
                    }
                    movingCell.classList.add("col-drop-highlight");
                    setTimeout(() => movingCell.classList.remove("col-drop-highlight"), 800);
                }
            });

            // Save order to localStorage
            const newOrder = Array.from(table.querySelectorAll("thead th")).map(getColumnKey);
            localStorage.setItem(localStorageKey, JSON.stringify(newOrder));

            const resetBtnEl = document.getElementById("btnResetColOrder");
            if (resetBtnEl) resetBtnEl.style.display = "inline-flex";

            showAdminToast("success", "Порядок столбцов обновлен");
        });

        th.addEventListener("dragend", function () {
            if (draggedTh) draggedTh.classList.remove("col-dragging");
            table.querySelectorAll("thead th").forEach(t => t.classList.remove("col-drop-left", "col-drop-right"));
            draggedTh = null;
            draggedColIndex = -1;
        });
    });

    // -------------------------------------------------------------------------
    // C. Row Drag and Drop (with Auto-save to Backend)
    // -------------------------------------------------------------------------
    const hasOrderSupport = !!table.querySelector("th.column-order") || !!table.querySelector("td.field-order");
    if (!hasOrderSupport) return;

    let draggedRow = null;
    const tbodyRows = Array.from(table.querySelectorAll("tbody tr"));

    tbodyRows.forEach(function (tr) {
        // Add row handle in the action-checkbox column
        const cbCell = tr.querySelector("td.action-checkbox");
        if (cbCell && !cbCell.querySelector(".admin-row-drag-handle")) {
            const handle = document.createElement("span");
            handle.className = "admin-row-drag-handle";
            handle.title = "Перетащите для изменения порядка строк";
            handle.innerHTML = '<i class="bi bi-grip-vertical"></i>';
            handle.setAttribute("draggable", "true");

            const wrapper = document.createElement("div");
            wrapper.className = "admin-checkbox-cell";
            while (cbCell.firstChild) {
                wrapper.appendChild(cbCell.firstChild);
            }
            wrapper.insertBefore(handle, wrapper.firstChild);
            cbCell.appendChild(wrapper);

            handle.addEventListener("dragstart", function (e) {
                draggedRow = tr;
                tr.classList.add("row-dragging");
                e.dataTransfer.effectAllowed = "move";
                e.dataTransfer.setData("text/plain", tr.querySelector("input.action-select")?.value || "");
                e.stopPropagation();
            });
        }

        tr.setAttribute("draggable", "true");

        tr.addEventListener("dragstart", function (e) {
            // Cancel if clicking on form controls or links
            if (e.target.closest("input") || e.target.closest("select") || e.target.closest("textarea") || e.target.closest("a")) {
                e.preventDefault();
                return;
            }
            draggedRow = tr;
            tr.classList.add("row-dragging");
            e.dataTransfer.effectAllowed = "move";
            e.dataTransfer.setData("text/plain", tr.querySelector("input.action-select")?.value || "");
        });

        tr.addEventListener("dragover", function (e) {
            if (!draggedRow || draggedRow === tr) return;
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";

            const rect = tr.getBoundingClientRect();
            const isBottom = (e.clientY - rect.top) > (rect.height / 2);
            tr.classList.remove("row-drop-top", "row-drop-bottom");
            tr.classList.add(isBottom ? "row-drop-bottom" : "row-drop-top");
        });

        tr.addEventListener("dragleave", function () {
            tr.classList.remove("row-drop-top", "row-drop-bottom");
        });

        tr.addEventListener("drop", function (e) {
            if (!draggedRow || draggedRow === tr) return;
            e.preventDefault();
            const isBottom = tr.classList.contains("row-drop-bottom");
            tr.classList.remove("row-drop-top", "row-drop-bottom");

            if (isBottom) {
                tr.after(draggedRow);
            } else {
                tr.before(draggedRow);
            }

            // Update zebra striping
            const tbody = table.querySelector("tbody");
            const allRows = Array.from(tbody.querySelectorAll("tr"));
            allRows.forEach((r, idx) => {
                r.classList.remove("row1", "row2");
                r.classList.add(idx % 2 === 0 ? "row1" : "row2");
            });

            // Update visible order inputs in DOM
            const orderInputs = allRows.map(r => r.querySelector('input[name$="-order"]')).filter(Boolean);
            const currentValues = orderInputs.map(inp => parseInt(inp.value, 10)).filter(v => !isNaN(v));
            currentValues.sort((a, b) => a - b);
            orderInputs.forEach((inp, idx) => {
                if (idx < currentValues.length) {
                    inp.value = currentValues[idx];
                }
            });

            // Extract IDs in new sequence
            const orderedIds = allRows.map(r => {
                return r.querySelector("input.action-select")?.value;
            }).filter(Boolean);

            // Send reorder request to backend
            const reorderUrl = pathname.replace(/\/+$/, "") + "/reorder/";
            const csrfToken = getAdminCsrfToken();

            fetch(reorderUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({ ordered_ids: orderedIds })
            })
            .then(res => {
                if (!res.ok) throw new Error("HTTP " + res.status);
                return res.json();
            })
            .then(data => {
                if (data.status === "success") {
                    showAdminToast("success", data.message || "Порядок товаров успешно сохранен");
                    if (data.orders) {
                        allRows.forEach(r => {
                            const id = r.querySelector("input.action-select")?.value;
                            const inp = r.querySelector('input[name$="-order"]');
                            if (id && inp && data.orders[id] !== undefined) {
                                inp.value = data.orders[id];
                            }
                        });
                    }
                    draggedRow.classList.add("row-reordered-success");
                    setTimeout(() => draggedRow.classList.remove("row-reordered-success"), 1200);
                } else {
                    showAdminToast("error", data.message || "Ошибка при сохранении порядка");
                }
            })
            .catch(err => {
                console.error("Reorder request failed:", err);
                showAdminToast("error", "Не удалось сохранить порядок на сервере");
            });
        });

        tr.addEventListener("dragend", function () {
            if (draggedRow) draggedRow.classList.remove("row-dragging");
            table.querySelectorAll("tbody tr").forEach(r => r.classList.remove("row-drop-top", "row-drop-bottom"));
            draggedRow = null;
        });
    });
}


