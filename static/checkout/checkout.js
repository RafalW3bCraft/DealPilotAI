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
    quoteForm.addEventListener('submit', function (event) {
      event.preventDefault();
      var items = [];
      var message = document.getElementById('dp-quote-msg');
      var invalidQuantity = null;
      quoteForm.querySelectorAll('input[name="sel"]:checked').forEach(function (checkbox) {
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
          if (result.status === 202) {
            setMessage(
              message,
              result.body.detail || 'Your existing checkout is being recovered. Retry shortly; no duplicate order was created.',
              'error'
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

  var expiryElement = document.getElementById('dp-expiry');
  if (expiryElement) {
    var expiryTimestamp = parseInt(expiryElement.getAttribute('data-expires'), 10);
    var countdown = document.getElementById('dp-countdown');
    if (countdown && expiryTimestamp > 0) {
      var updateCountdown = function () {
        var secondsLeft = expiryTimestamp - Math.floor(Date.now() / 1000);
        if (secondsLeft <= 0) {
          countdown.textContent = '(expired)';
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
