
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

onResizeWindow = (event)=>
	videoWidth = 800
	videoHeight = 450
	finalWidth = Math.min(window.innerWidth - 100, videoWidth)
	finalHeight = Math.min(videoHeight * finalWidth / videoWidth, videoHeight)
	$('#intro-video iframe').width(finalWidth).height(finalHeight)
	return

sectionIndex = 0
nQuestions = 4
nSections = 6
sliderSize = 250
finished = false

validateEmail = (email)->
  re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return re.test(email)

closeLoginForm = ()->
	loginForm = $('#login-form')
	loginForm.hide().removeClass('visible')
	$('#background').addClass('hidden')
	return

closeSelectEdition = ()->
	selectEditionForm = $('#select-edition')
	selectEditionForm.hide().removeClass('visible')
	$('#background').addClass('hidden')
	return

loadLoginForm = ()->

	# $('.cd-footer').hide()
	finished = true

	$.get( "accounts/login/", ( data )=>
		parser = new DOMParser()
		doc = parser.parseFromString(data.html, "text/html")

		$('#login-form').html( doc.getElementById('login_form') )
		
		$('#id_login').attr('placeholder', "Nom d'utilisateur ou email")
		$('#id_username').attr('placeholder', "Nom d'utilisateur")
		$('label[for="id_remember"]').text('se souvenir de moi').css({'margin-left': '10px'}).parent().css( { 'display': 'flex', 'flex-direction': 'row-reverse' } )

		localStorage.setItem('just-logged-in', 'true')
		localStorage.setItem('selected-edition', location.pathname)

		closeButton = $('<button>').text('x').addClass('close-button').click(closeLoginForm)
		$('#login-form').prepend(closeButton)
		$('#login-form').removeClass('hidden').show().addClass('visible')
		return
	)

	return true


$(document).ready () ->
	
	# $('.section.cd-green').css( 'background': 'url(static/css/pattern-green.png) repeat 0 0' )

	red = '#F44336'
	blue = '#2196F3' # '#448AFF'
	green = '#8BC34A' # 'url(static/css/pattern-green.png) repeat 0 0' # '#8BC34A'
	yellow = '#FFC107'
	brown = '#795548'
	black = '#000000'
	white = '#FFFFFF'
	colors = [white]

	# fullPage = new fullpage('#fullpage', {
	# 	sectionsColor: colors, 			# ['#f2f2f2', '#4BBFC3', '#7BAABE', 'whitesmoke', '#000'],
	# 	anchors: ['introduction', 'participer', 'participations'],
	# 	loopHorizontal: false,
	# 	# dragAndMove: true,
	# 	navigation: true,
	# 	navigationPosition: 'right',
	# 	navigationTooltips: ['introduction', 'participer', 'participations'],
	# 	slidesNavigation: true
	# 	controlArrows: false

	# 	onSlideLeave: (section, origin, destination, direction)=>
	# 		console.log(section, origin, destination, direction)
	# 		return
	# })

	# fullpage_api.setAllowScrolling(false)
	
	onResizeWindow()

	window.onresize = onResizeWindow

	justLoggedIn = localStorage.getItem('just-logged-in') == 'true'
	
	if justLoggedIn
		localStorage.removeItem('just-logged-in')

	if localStorage.getItem('selected-edition') != null && justLoggedIn && $('body').attr('data-authenticated') == 'True'
		window.location = localStorage.getItem('selected-edition')
		return

	buttons = $('.editions li').each (index, element)=>
		buttonHref = $(element).find('a').attr('href')
		$(element).click (e)=>
			localStorage.setItem('selected-edition', buttonHref)
			return
	
	$('#login-button').click (event)->
		$('#background').removeClass('hidden')
		loadLoginForm()
		event.stopPropagation()
		event.preventDefault()
		return -1

	document.addEventListener("click", (event)->
		loginForm = $('#login-form')
		if loginForm.get(0) != event.target and (not jQuery.contains( loginForm.get(0), event.target )) and loginForm.hasClass('visible')
			closeLoginForm()
		
		selectEditionForm = $('#select-edition')
		if selectEditionForm.get(0) != event.target and (not jQuery.contains( selectEditionForm.get(0), event.target )) and selectEditionForm.hasClass('visible')
			closeSelectEdition()

		return)

	$('#select-edition .close-button').click(closeSelectEdition)

	$('#app-button').click (event)->
		# location.pathname = 'demo'
		$('#select-edition').removeClass('hidden').show().addClass('visible')
		$('#background').removeClass('hidden')
		event.stopPropagation()
		event.preventDefault()
		return -1

	# $('.next-button').click (event)->
	# 	fullpage_api.moveSectionDown()
	# 	return

	$('#id_email').on("change paste keyup", ()->
		text = $(this).val()
	
		if validateEmail(text)
			$('.cd-validate').removeClass('hidden').show()
		else
			$('.cd-validate').hide()
		return
	)

			
	return