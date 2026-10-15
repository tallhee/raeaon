(function (window, document) {
    "use strict";

    var TOKEN_NAME = "csrfToken";
    var HEADER_NAME = "X-CSRF-TOKEN";

    function getToken() {
        var meta = document.querySelector("meta[name='csrf-token']");
        return meta ? meta.getAttribute("content") : "";
    }

    function isSameOrigin(url) {
        if (!url) {
            return true;
        }
        var anchor = document.createElement("a");
        anchor.href = url;
        return (!anchor.protocol || anchor.protocol === window.location.protocol)
                && (!anchor.host || anchor.host === window.location.host);
    }

    function addTokenToForm(form) {
        var token = getToken();
        var method = (form.getAttribute("method") || "get").toLowerCase();
        var action = form.getAttribute("action") || window.location.href;
        if (!token || method !== "post" || !isSameOrigin(action)) {
            return;
        }

        var input = form.querySelector("input[name='" + TOKEN_NAME + "']");
        if (!input) {
            input = document.createElement("input");
            input.type = "hidden";
            input.name = TOKEN_NAME;
            form.appendChild(input);
        }
        input.value = token;
    }

    // Native/multipart save functions can explicitly add the token before submit.
    window.addCsrfTokenToForm = addTokenToForm;

    document.addEventListener("submit", function (event) {
        addTokenToForm(event.target);
    }, true);

    if (window.HTMLFormElement && window.HTMLFormElement.prototype.submit) {
        var nativeSubmit = window.HTMLFormElement.prototype.submit;
        window.HTMLFormElement.prototype.submit = function () {
            addTokenToForm(this);
            return nativeSubmit.apply(this, arguments);
        };
    }

    if (window.jQuery) {
        window.jQuery(document).ajaxSend(function (event, xhr, settings) {
            var token = getToken();
            var method = (settings.type || "GET").toUpperCase();
            if (token && method === "POST" && !settings.crossDomain) {
                xhr.setRequestHeader(HEADER_NAME, token);
            }
        });

        window.jQuery(document).ajaxError(function (event, xhr) {
            if (xhr.status !== 403) {
                return;
            }

            var redirectUrl = xhr.getResponseHeader("X-CSRF-REDIRECT");
            if (redirectUrl) {
                window.location.replace(redirectUrl);
            }
        });
    }
}(window, document));
