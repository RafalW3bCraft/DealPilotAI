/* DealPilot storefront interactions. Dynamic provider text is rendered as text,
 * never parsed as HTML. */
(function () {
  'use strict';

  function getCsrf() {
    return fetch('/api/csrf', { credentials: 'same-origin' })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Could not verify this session. Reload the page and try again.');
        }
        return response.json();
      })
      .then(function (data) {
        if (!data.csrf_token) {
          throw new Error('This session needs to be refreshed. Reload the page and try again.');
        }
        return data.csrf_token;
      });
  }

  function postJson(url, body) {
    return getCsrf().then(function (token) {
      return fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': token
        },
        body: JSON.stringify(body)
      }).then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, status: response.status, body: data };
        }, function () {
          return {
            ok: false,
            status: response.status,
            body: { error: 'The server returned an unreadable response. Try again.' }
          };
        });
      });
    });
  }

  function setMessage(element, message, state) {
    if (!element) { return; }
    element.textContent = message || '';
    if (state) {
      element.setAttribute('data-state', state);
    } else {
      element.removeAttribute('data-state');
    }
  }

  function setBusy(element, busy, label) {
    if (!element) { return; }
    if (busy) {
      if (!element.hasAttribute('data-idle-label')) {
        element.setAttribute('data-idle-label', element.textContent.trim());
      }
      element.disabled = true;
      element.classList.add('is-loading');
      element.textContent = label;
    } else {
      element.disabled = false;
      element.classList.remove('is-loading');
      var idleLabel = element.getAttribute('data-idle-label');
      if (idleLabel) { element.textContent = idleLabel; }
    }
  }

  function appendText(parent, tagName, className, value) {
    var element = document.createElement(tagName);
    if (className) { element.className = className; }
    element.textContent = value == null ? '' : String(value);
    parent.appendChild(element);
    return element;
  }

  var selectionKey = 'dealpilot-cart-selection';
  function saveSelection() {
    var form = document.getElementById('dp-quote-form');
    if (!form) { return; }
    var selected = [];
    form.querySelectorAll('input[name="sel"]').forEach(function (input) {
      if (input.type === 'checkbox' && !input.checked) { return; }
      var quantity = Array.from(form.querySelectorAll('input[name^="qty_"]'))
        .find(function (field) { return field.name === 'qty_' + input.value; });
      selected.push({ sku: input.value, quantity: quantity ? quantity.value : '1' });
    });
    try { sessionStorage.setItem(selectionKey, JSON.stringify(selected)); } catch (_) { /* Storage can be disabled. */ }
  }

  function sameOriginOrderUrl(value) {
    try {
      var url = new URL(value, window.location.origin);
      return url.origin === window.location.origin && /^\/orders\/[^/]+$/.test(url.pathname) ? url.href : null;
    } catch (_) { return null; }
  }

  function renderRecommendations(container, response) {
    container.replaceChildren();
    if (response.ai_disclaimer) {
      appendText(container, 'p', 'dp-alert dp-alert-warn dp-ai-disclaimer', response.ai_disclaimer);
    }
    var items = Array.isArray(response.items) ? response.items : [];
    items.forEach(function (item) {
      var card = document.createElement('article');
      card.className = 'dp-ai-card';
      appendText(card, 'h3', '', item.sku || 'Catalog product');
      appendText(card, 'p', 'dp-card-price', (item.price || '') + ' ' + (item.currency || ''));
      appendText(card, 'p', 'dp-card-reason', item.reason || '');
      var checkbox = Array.from(document.querySelectorAll('#dp-quote-form input[name="sel"]'))
        .find(function (input) { return input.value === item.sku && !input.disabled; });
      if (checkbox) {
        var title = checkbox.closest('.dp-card').querySelector('.dp-card-title');
        card.querySelector('h3').textContent = title.textContent;
        var choose = appendText(card, 'button', 'dp-btn dp-btn-secondary dp-recommend-add', checkbox.checked ? 'Selected in your cart' : 'Add to your cart');
        choose.type = 'button';
        choose.setAttribute('aria-pressed', String(checkbox.checked));
        choose.addEventListener('click', function () {
          checkbox.checked = !checkbox.checked;
          choose.setAttribute('aria-pressed', String(checkbox.checked));
          choose.textContent = checkbox.checked ? 'Selected in your cart' : 'Add to your cart';
          saveSelection();
          setMessage(document.getElementById('dp-quote-msg'), checkbox.checked ? 'Product selected. Review your cart below.' : 'Product removed from your selection.');
        });
      }
      container.appendChild(card);
    });
    if (response.tradeoffs) {
      appendText(container, 'p', 'dp-ai-extra', response.tradeoffs);
    }
    if (Array.isArray(response.missing_info) && response.missing_info.length) {
      var list = document.createElement('ul');
      list.className = 'dp-ai-missing';
      response.missing_info.forEach(function (message) {
        appendText(list, 'li', '', message);
      });
      container.appendChild(list);
    }
    if (!items.length && !response.tradeoffs && !response.ai_disclaimer) {
      appendText(container, 'p', 'dp-muted', 'No catalog matches yet. Try a different description.');
    }
  }

  var aiForm = document.getElementById('dp-ai-form');
  if (aiForm) {
    aiForm.addEventListener('submit', function (event) {
      event.preventDefault();
      var queryInput = document.getElementById('dp-ai-query');
      var button = aiForm.querySelector('button[type="submit"]');
      var output = document.getElementById('dp-ai-results');
      var query = queryInput.value.trim();
      if (!query) {
        queryInput.focus();
        return;
      }

      setBusy(button, true, 'Finding options…');
      aiForm.setAttribute('aria-busy', 'true');
      output.setAttribute('aria-busy', 'true');
      output.replaceChildren();
      appendText(output, 'p', 'dp-muted', 'Searching the merchant catalog…');

      postJson('/api/ai/recommend', { query: query })
        .then(function (result) {
          if (!result.ok) {
            output.replaceChildren();
            appendText(output, 'p', 'dp-alert dp-alert-error', result.body.error || 'Recommendations are unavailable right now.');
            return;
          }
          renderRecommendations(output, result.body);
        })
        .catch(function (error) {
          output.replaceChildren();
          appendText(output, 'p', 'dp-alert dp-alert-error', error.message || 'Network error. Please try again.');
        })
        .then(function () {
          aiForm.removeAttribute('aria-busy');
          output.removeAttribute('aria-busy');
          setBusy(button, false);
        });
    });
  }

  var quoteForm = document.getElementById('dp-quote-form');
  if (quoteForm) {
    if (quoteForm.querySelector('input[type="checkbox"][name="sel"]')) {
      try {
        var saved = JSON.parse(sessionStorage.getItem(selectionKey) || '[]');
        if (Array.isArray(saved)) {
          saved.forEach(function (item) {
            var checkbox = Array.from(quoteForm.querySelectorAll('input[name="sel"]'))
              .find(function (input) { return input.value === item.sku && !input.disabled; });
            if (!checkbox) { return; }
            checkbox.checked = true;
            var quantity = Array.from(quoteForm.querySelectorAll('input[name^="qty_"]'))
              .find(function (input) { return input.name === 'qty_' + item.sku; });
            if (quantity && Number.isSafeInteger(Number(item.quantity)) && Number(item.quantity) >= 1 && Number(item.quantity) <= Number(quantity.max)) {
              quantity.value = item.quantity;
            }
          });
        }
      } catch (_) { /* A fresh selection is safe when browser storage is unavailable. */ }
    }
    quoteForm.addEventListener('input', function () {
      saveSelection();
      var button = document.getElementById('dp-checkout-btn');
      if (button) {
        button.disabled = true;
        setMessage(document.getElementById('dp-checkout-msg'), 'Update your cart total to confirm these quantities before checkout.');
      }
    });
    quoteForm.addEventListener('submit', function (event) {
      event.preventDefault();
      var items = [];
      var message = document.getElementById('dp-quote-msg');
      var invalidQuantity = null;
      quoteForm.querySelectorAll('input[name="sel"]').forEach(function (checkbox) {
        if (checkbox.type === 'checkbox' && !checkbox.checked) { return; }
        var sku = checkbox.getAttribute('data-sku');
        var quantityInput = Array.from(quoteForm.querySelectorAll('input[name^="qty_"]'))
          .find(function (input) { return input.name === 'qty_' + sku; });
        var quantity = quantityInput ? Number(quantityInput.value) : 1;
        if (!Number.isSafeInteger(quantity) || quantity < 1 ||
            (quantityInput && !quantityInput.checkValidity())) {
          invalidQuantity = quantityInput;
          return;
        }
        items.push({ sku: sku, quantity: quantity });
      });
      if (invalidQuantity) {
        setMessage(message, 'Enter a valid whole-number quantity for each selected product.', 'error');
        invalidQuantity.focus();
        return;
      }
      if (!items.length) {
        setMessage(message, 'Choose at least one product to create your cart.', 'error');
        var firstAvailable = quoteForm.querySelector('input[name="sel"]:not(:disabled)');
        if (firstAvailable) { firstAvailable.focus(); }
        return;
      }

      saveSelection();
      var submitButton = quoteForm.querySelector('button[type="submit"]');
      setMessage(message, 'Checking current prices and availability…');
      setBusy(submitButton, true, 'Building your cart…');
      quoteForm.setAttribute('aria-busy', 'true');
      postJson('/cart/quote', { items: items })
        .then(function (result) {
          if (!result.ok) {
            setMessage(message, result.body.error || 'Could not create your cart.', 'error');
            return;
          }
          if (result.body.redirect) {
            window.location.assign(result.body.redirect);
            return;
          }
          setMessage(message, 'The cart could not be opened. Please try again.', 'error');
        })
        .catch(function (error) {
          setMessage(message, error.message || 'Network error creating your cart.', 'error');
        })
        .then(function () {
          quoteForm.removeAttribute('aria-busy');
          setBusy(submitButton, false);
        });
    });
  }

  var checkoutButton = document.getElementById('dp-checkout-btn');
  if (checkoutButton) {
    checkoutButton.addEventListener('click', function () {
      var message = document.getElementById('dp-checkout-msg');
      var quoteId = checkoutButton.getAttribute('data-quote-id');
      setMessage(message, 'Preparing your PayPal sandbox order…');
      setBusy(checkoutButton, true, 'Connecting to PayPal…');
      postJson('/checkout/start', { quote_id: quoteId })
        .then(function (result) {
          var orderUrl = sameOriginOrderUrl(result.body.order_url);
          if (orderUrl && (result.status === 202 || ['PAID', 'FAILED', 'CANCELED'].indexOf(result.body.status) !== -1)) {
            window.location.assign(orderUrl);
            return;
          }
          if (result.status === 202) {
            setMessage(
              message,
              result.body.detail || 'Your existing checkout is being recovered. Retry shortly; no duplicate order was created.',
              'pending'
            );
            return;
          }
          if (!result.ok) {
            setMessage(message, result.body.detail || result.body.error || 'Checkout could not be started. Please try again.', 'error');
            return;
          }
          if (result.body.approve_url) {
            window.location.assign(result.body.approve_url);
            return;
          }
          setMessage(message, 'PayPal approval is not available yet. Retry shortly.', 'error');
        })
        .catch(function (error) {
          setMessage(message, error.message || 'Network error starting checkout.', 'error');
        })
        .then(function () {
          setBusy(checkoutButton, false);
        });
    });
  }

  var orderPanel = document.getElementById('dp-order-status');
  if (orderPanel && orderPanel.dataset.statusUrl) {
    var refreshButton = document.getElementById('dp-order-refresh');
    var orderMessage = document.getElementById('dp-order-message');
    var pollCount = 0;
    var maxPolls = 8;
    var pollTimer = null;
    var requestPending = false;
    var finalStates = ['PAID', 'FAILED', 'CANCELED'];
    var refreshOrder = function () {
      if (requestPending) { return; }
      window.clearTimeout(pollTimer);
      requestPending = true;
      pollCount += 1;
      setBusy(refreshButton, true, 'Checking order…');
      fetch(orderPanel.dataset.statusUrl, { credentials: 'same-origin', cache: 'no-store' })
        .then(function (response) {
          if (!response.ok) { throw new Error('Could not check your order. Keep this page link and try Refresh order status again.'); }
          return response.json();
        })
        .then(function (order) {
          if (order.status && order.status !== orderPanel.dataset.status) {
            window.location.reload();
            return;
          }
          if (finalStates.indexOf(order.status) !== -1) {
            setMessage(orderMessage, 'Order status is up to date.');
            return;
          }
          if (pollCount < maxPolls) {
            setMessage(orderMessage, 'Awaiting verified payment confirmation. Checking again shortly…', 'pending');
            pollTimer = window.setTimeout(refreshOrder, 5000);
          } else {
            setMessage(orderMessage, 'Confirmation is taking longer. Automatic checks have paused. Keep this order link and use Refresh order status, or contact the merchant. Do not start another payment.', 'pending');
          }
        })
        .catch(function (error) { setMessage(orderMessage, error.message || 'Unable to check your order. Try refreshing its status.', 'error'); })
        .then(function () { requestPending = false; setBusy(refreshButton, false); });
    };
    refreshButton.addEventListener('click', refreshOrder);
    if (finalStates.indexOf(orderPanel.dataset.status) === -1) { pollTimer = window.setTimeout(refreshOrder, 2000); }
    window.addEventListener('pagehide', function () { window.clearTimeout(pollTimer); });
  }

  var expiryElement = document.getElementById('dp-expiry');
  if (expiryElement) {
    var expiryTimestamp = parseInt(expiryElement.getAttribute('data-expires'), 10);
    var countdown = document.getElementById('dp-countdown');
    if (countdown && expiryTimestamp > 0) {
      var updateCountdown = function () {
        var secondsLeft = expiryTimestamp - Math.floor(Date.now() / 1000);
        if (secondsLeft <= 0) {
          countdown.textContent = '(expired)';
          if (checkoutButton) { checkoutButton.disabled = true; }
          setMessage(document.getElementById('dp-checkout-msg'), 'This quote expired. Update your cart total to continue.', 'error');
          return;
        }
        var minutes = Math.floor(secondsLeft / 60);
        var seconds = secondsLeft % 60;
        countdown.textContent = '(expires in ' + minutes + 'm ' + seconds + 's)';
        window.setTimeout(updateCountdown, 1000);
      };
      updateCountdown();
    }
  }
})();
