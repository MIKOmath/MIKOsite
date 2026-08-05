/*
 * Mobile navigation for the shared site header.
 *
 * Ships with the header partial rather than from a page-level bundle, so the menu
 * works everywhere the header renders. It previously lived in script.js, which
 * about half the pages never loaded -- their hamburger button did nothing.
 */
(function () {
    function init() {
        var toggle = document.querySelector('.site-nav__toggle');
        var menu = document.querySelector('.site-nav__menu');

        if (!toggle || !menu) {
            return;
        }

        function setOpen(open) {
            menu.classList.toggle('is-open', open);
            toggle.setAttribute('aria-expanded', String(open));
        }

        toggle.addEventListener('click', function () {
            setOpen(!menu.classList.contains('is-open'));
        });

        menu.addEventListener('click', function (event) {
            if (event.target.closest('a')) {
                setOpen(false);
            }
        });

        document.addEventListener('click', function (event) {
            if (!menu.classList.contains('is-open')) {
                return;
            }
            if (!menu.contains(event.target) && !toggle.contains(event.target)) {
                setOpen(false);
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && menu.classList.contains('is-open')) {
                setOpen(false);
                toggle.focus();
            }
        });

        /* Resizing past the breakpoint hides the toggle, which would otherwise strand
           the menu in its open state with no way to close it. */
        var desktop = window.matchMedia('(min-width: 1001px)');
        desktop.addEventListener('change', function (event) {
            if (event.matches) {
                setOpen(false);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
