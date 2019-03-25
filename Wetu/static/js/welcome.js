// Generated by CoffeeScript 1.10.0
(function() {
  $(document).ready(function() {
    var buttons, justLoggedIn;
    justLoggedIn = localStorage.getItem('just-logged-in') === 'true';
    if (justLoggedIn) {
      localStorage.removeItem('just-logged-in');
    }
    if (localStorage.getItem('selected-edition') !== null && justLoggedIn && $('.editions').attr('data-authenticated') === 'True') {
      window.location = localStorage.getItem('selected-edition');
      return;
    }
    buttons = $('.editions li').each((function(_this) {
      return function(index, element) {
        var buttonHref;
        buttonHref = $(element).find('a').attr('href');
        return $(element).click(function(e) {
          localStorage.setItem('selected-edition', buttonHref);
        });
      };
    })(this));
  });

}).call(this);
