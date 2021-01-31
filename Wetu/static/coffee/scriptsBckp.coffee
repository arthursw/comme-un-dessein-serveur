state = 'Email'
previousState = 'Start'
userIsKnown = false
# createAccount = false

$.ajaxSetup beforeSend: (xhr, settings) ->

	getCookie = (name) ->
		cookieValue = null
		if document.cookie and document.cookie != ''
			cookies = document.cookie.split(';')
			i = 0
			while i < cookies.length
				cookie = jQuery.trim(cookies[i])
				# Does this cookie string begin with the name we want?
				if cookie.substring(0, name.length + 1) == name + '='
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
					break
				i++
		cookieValue

	if !(/^http:.*/.test(settings.url) or /^https:.*/.test(settings.url))
		# Only send the token to relative URLs i.e. locally.
		xhr.setRequestHeader 'X-CSRFToken', getCookie('csrftoken')
	return


$(document).ready ()->
	$('label[for="id_remember"]').text('se sourvenir de moi').parent().css( 'display': 'flex', 'flex-direction': 'row-reverse' )
	return











# $(document).ready () ->
# 	errors = $('.errorlist').text()
# 	console.log(errors)

# 	# if window.location.pathname == "/accounts/login/" and errors == "L’adresse e-mail ou le mot de passe sont incorrects."
# 		# window.location = "/connexion/#wrongPassword"

# 	if window.location.pathname == "/accounts/signup/"
# 		window.location = "/connexion/"

# 	# if window.location.pathname != '/connexion/'
# 	# 	$('.form-signin-heading').removeClass('cd-hidden').show()

# 	signupLabelJ = $('#cd-signup-label')
# 	signinLabelJ = $('#cd-signin-label')
# 	signupButtonJ = $('#cd-signup')
# 	signinButtonJ = $('#cd-signin')
# 	primaryButtonJ = $('#cd-submit')
# 	loadIconJ = primaryButtonJ.find('.glyphicon')
# 	loadIconJ.hide()
# 	loadIconJ.removeClass('cd-hidden')
# 	emailJ = $('#cd-email')
# 	usernameJ = $('#cd-username')
# 	passwordJ = $('#cd-password')
# 	maskJ = $('#cd-mask')
# 	passwordGroupJ = $('#cd-password-group')
# 	labelJ = $('#cd-label span')
# 	titleJ = $('#cd-title span')
# 	backJ = $('#cd-cancel')
# 	# buttonListJ = $('ul.button-list')
# 	# orJ = $('.cd-or')
# 	errorJ = $('#cd-error')

# 	# start = (newAccount)->
# 	# 	createAccount = newAccount
# 	# 	$('div.cd-signup-signin').hide()
# 	# 	labelJ.show()
# 	# 	emailJ.show()
# 	# 	primaryButtonJ.show()
# 	# 	backJ.show()
# 	# 	if createAccount
# 	# 		emailJ.attr('placeholder', "Email ou nom d'utilisateur")
# 	# 	else
# 	# 		emailJ.attr('placeholder', "Adresse Email")
# 	# 	deferredFocus(emailJ)
# 	# 	state = 'Email'
# 	# 	return

# 	# signupButtonJ.click(()->start(true))
# 	# signinButtonJ.click(()->start(false))

# 	submitEnter = (event)->
# 		switch event.keyCode
# 			when 13 				# enter
# 				primaryButtonJ.click()
# 		return
	
# 	deferredFocus = (divToFocusJ)->
# 		setTimeout (()-> divToFocusJ.focus()), 500
# 		return

# 	validateEmail = (email) ->
# 		re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
# 		re.test email

# 	setState = (newState)->
# 		previousState = state
# 		state = newState
# 		return



# 	emailJ.focus()
# 	emailJ.keyup(submitEnter)
# 	passwordJ.keyup(submitEnter)
# 	usernameJ.keyup(submitEnter)

# 	maskJ.click (event)->
# 		masked = passwordJ.attr('type') == 'password'
# 		if masked
# 			passwordJ.attr('type', 'text')
# 			maskJ.text('Masquer')
# 		else
# 			passwordJ.attr('type', 'password')
# 			maskJ.text('Afficher')
# 		return

# 	if window.location.hash == '#wrongPassword'
# 		setState('Password')
# 		userIsKnown = true
# 		emailJ.hide()
# 		# orJ.hide()
# 		backJ.show()
# 		labelJ.text("Mot de passe :")
# 		passwordGroupJ.removeClass('cd-hidden').show()
# 		errorJ.removeClass('cd-hidden').show().find('span').text("L’adresse e-mail ou le mot de passe sont incorrects.")
# 		deferredFocus(passwordJ)
	
# 	primaryButtonJ.click (event)->
# 		if state == 'Start'
# 			console.log('continue')
# 		else if state == 'Email'

# 			# do things if email is invalid

# 			email = emailJ.val()

# 			if email.length <= 0
# 				console.error('This email adress is empty')
# 				errorJ.removeClass('cd-hidden').show().find('span').text("Veuillez entrer une adresse email ou un nom d'utilisateur.")
# 				emailJ.select()
# 				deferredFocus(emailJ)
# 				return

# 			errorJ.hide()

# 			loadIconJ.show()
# 			$.ajax( method: "POST", url: "ajaxCall/", data: data: JSON.stringify { function: 'isEmailKnown', args: { email: email } } ).done (result)->
# 				loadIconJ.hide()
# 				if result.message?
# 					console.log(result.message)
				
# 				email = emailJ.val()

# 				userIsKnown = result.emailIsKnown or result.usernameIsKnown
				
# 				if not userIsKnown
# 					if not validateEmail(email)
# 						errorJ.removeClass('cd-hidden').show().find('span').text("Cette adresse email n'est pas valide.")
# 						emailJ.select()
# 						deferredFocus(emailJ)
# 						return

# 				emailJ.hide()
# 				# buttonListJ.hide()
# 				# orJ.hide()
# 				backJ.show()

# 				if not userIsKnown
# 					titleJ.text('Créer un compte')
# 					$('#id_login, #id_email').val(email)
# 					username = email.substr(0, email.indexOf('@'))
# 					if result.emailShortNameIsKnown 
# 						username += Math.random().toFixed(2).substring(2)
# 					usernameJ.val(username)
# 					setState('AcceptEmails')
# 					labelJ.html('<p>En poursuivant votre navigation sur ce site, vous acceptez de recevoir des emails, ainsi que l’utilisation de cookies pour vous connecter, réaliser des statistiques de visites, et lorsque vous partagez du contenu sur les réseaux sociaux.</p><a href="">Conditions d\'utilisation</a>')
# 					deferredFocus(primaryButtonJ.focus())
# 				else
# 					titleJ.text('Se connecter')
# 					if result.emailIsKnown
# 						$('#id_email, #id_login').val(email)
# 					else if result.usernameIsKnown
# 						$('#id_login').val(email)
# 					setState('Password')
# 					labelJ.text("Mot de passe :")
# 					passwordGroupJ.removeClass('cd-hidden').show()
# 					maskJ.text('Afficher')
# 					passwordJ.attr('type', 'password')
# 					deferredFocus(passwordJ)
				
# 				return
# 		else if state == 'AcceptEmails'

# 			setState('Username')
# 			labelJ.text("Nom d'utilisateur :")
# 			usernameJ.removeClass('cd-hidden').show()
# 			deferredFocus(usernameJ)

# 		else if state == 'Username'
			
# 			username = usernameJ.val()
# 			errorJ.hide()
# 			loadIconJ.show()
# 			$.ajax( method: "POST", url: "ajaxCall/", data: data: JSON.stringify { function: 'isUsernameKnown', args: { username: username } } ).done (result)->
# 				loadIconJ.hide()
# 				if result.message?
# 					console.log(result.message)

# 				if result.usernameIsKnown
# 					console.error('The username is already taken')
# 					errorJ.removeClass('cd-hidden').show().find('span').text('Un utilisateur avec ce nom existe déjà.')
# 					usernameJ.select()
# 					deferredFocus(usernameJ)
# 				else
# 					setState('Password')
# 					labelJ.text("Mot de passe :")

# 					$('#id_username').val(usernameJ.val())

# 					usernameJ.hide()
					
# 					passwordJ.val(Math.random().toFixed(4).substring(2))

# 					maskJ.text('Masquer')
# 					passwordJ.attr('type', 'text')

# 					passwordGroupJ.removeClass('cd-hidden').show()
# 					deferredFocus(passwordJ)
# 				return
			
# 		else if state == 'Password'
# 			# setState('End')

# 			errorJ.hide()

# 			# do things if password is empty
			
# 			password = passwordJ.val()

# 			if password.length <= 2
# 				console.error('The password is too short')
# 				errorJ.removeClass('cd-hidden').show().find('span').text('Le mot de passe est trop court.')
# 				passwordJ.select()
# 				deferredFocus(passwordJ)
# 				return

# 			$('#id_password, #id_password1').val(password)

# 			localStorage.setItem('just-logged-in', 'true')
			
# 			if userIsKnown
# 				$('#submit-signin').click()
# 			else
# 				$('#submit-signup').click()
			
# 		return

# 	backJ.click (event)->
		
# 		errorJ.hide()
		
# 		if state == 'Start'
# 			window.location = '/'
# 		else if state == 'Email'			
# 			# buttonListJ.hide()
# 			# $('div.cd-signup-signin').removeClass('cd-hidden').show()
# 			# emailJ.hide()
# 			# backJ.hide()
# 			# primaryButtonJ.hide()
# 			window.location = '/'
		
# 		else if state == 'Username' or state == 'AcceptEmails'
# 			setState('Email')
			
# 			titleJ.text('Créer un compte ou se connecter')
# 			labelJ.text("Email ou nom d'utilisateur :")

# 			usernameJ.hide()
# 			passwordGroupJ.hide()

# 			emailJ.show()
# 			deferredFocus(emailJ)
# 			# buttonListJ.show()

# 		else if state == 'Password'

# 			passwordGroupJ.hide()

# 			if not userIsKnown
# 				setState('Username')
# 				labelJ.text("Nom d'utilisateur :")
# 				usernameJ.removeClass('cd-hidden').show()
# 				deferredFocus(usernameJ)
# 			else
# 				setState('Email')
# 				labelJ.text("Email ou nom d'utilisateur :")
# 				titleJ.text('Créer un compte ou se connecter')
# 				emailJ.show()
# 				deferredFocus(emailJ)

# 		return
# 	return