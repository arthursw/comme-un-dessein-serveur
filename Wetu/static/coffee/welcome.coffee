
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

sectionIndex = 0
nQuestions = 4
nSections = 6
sliderSize = 250
finished = false

validateEmail = (email)->
  re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return re.test(email)

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

		$('#login-form').removeClass('hidden').show().addClass('visible')
		return
	)

	return true

# surveyActions = {
# 	5: loadLoginForm
# }

# stateObject = {
# 	sectionIndex: sectionIndex
# }

# window.onpopstate = (event) ->
# 	console.log("location: " + document.location + ", state: " + JSON.stringify(event.state));
# 	sectionIndex = event.state.sectionIndex
# 	surveyActivateSection(false)
# 	return

# surveyActivateSection = (pushState=true)->
# 	# $('.cd-section').hide()
# 	sectionNumber = sectionIndex+1
# 	# $('.cd-section-' + sectionNumber).removeClass('hidden').show()
# 	# $('.cd-footer .progression').text(if sectionNumber <= nQuestions then sectionNumber + ' / ' + nQuestions else 'Terminé')
# 	# $('.cd-footer .bar').css( width: Math.min(sliderSize, sectionNumber * sliderSize / nQuestions) )
# 	$('.cd-validate').hide()

# 	# if pushState
# 	# 	stateObject.sectionIndex = sectionIndex
# 	# 	history.pushState(stateObject, "page " + sectionNumber)
# 	return

# surveyNext = ()->
# 	if finished or sectionIndex >= (nSections - 1) then return
# 	sectionNumber = sectionIndex+1
# 	if surveyActions[sectionNumber]? and not surveyActions[sectionNumber]() then return
# 	sectionIndex++
# 	surveyActivateSection()
# 	return

# surveyPrevious = ()->
# 	if finished or sectionIndex == 0 then return
# 	sectionIndex--
# 	surveyActivateSection()
# 	return

checkSurveyCompleted = ()->

	requiredSections = $('.cd-required')
	allSectionAnswered = true
	for requiredSection in requiredSections
		if $(requiredSection).find('.cd-radio.checked').length == 0
			allSectionAnswered = false
	
	if allSectionAnswered
		$('#survey-invalid').hide()
		$('#survey-email').removeClass('hidden').show()

	return

surveyNext = ()->
	fullpage_api.moveSlideRight()
	return

fullPage = null

$(document).ready () ->
	$('.section.cd-green').css( 'background': 'url(static/css/pattern-green.png) repeat 0 0' )

	red = '#F44336'
	blue = '#2196F3' # '#448AFF'
	green = '#8BC34A' # 'url(static/css/pattern-green.png) repeat 0 0' # '#8BC34A'
	yellow = '#FFC107'
	brown = '#795548'
	black = '#000000'
	colors = [green, green, yellow, blue,green, brown, black]

	fullPage = new fullpage('#fullpage', {
		sectionsColor: colors, 			# ['#f2f2f2', '#4BBFC3', '#7BAABE', 'whitesmoke', '#000'],
		anchors: ['introduction', 'participer', 'participations'],
		loopHorizontal: false,
		# dragAndMove: true,
		navigation: true,
		navigationPosition: 'right',
		navigationTooltips: ['introduction', 'participer', 'participations'],
		slidesNavigation: true
		controlArrows: false

		onSlideLeave: (section, origin, destination, direction)=>
			console.log(section, origin, destination, direction)
			return
	})

	# fullpage_api.setAllowScrolling(false)

	justLoggedIn = localStorage.getItem('just-logged-in') == 'true'
	
	if justLoggedIn
		localStorage.removeItem('just-logged-in')

	if localStorage.getItem('selected-edition') != null && justLoggedIn && $('.editions').attr('data-authenticated') == 'True'
		window.location = localStorage.getItem('selected-edition')
		return

	buttons = $('.editions li').each (index, element)=>
		buttonHref = $(element).find('a').attr('href')
		$(element).click (e)=>
			localStorage.setItem('selected-edition', buttonHref)
			return
	
	$('#login-button').click (event)->
		loadLoginForm()
		return

	document.addEventListener("click", (event)->
		loginForm = $('#login-form')
		if loginForm.get(0) != event.target and (not jQuery.contains( loginForm.get(0), event.target )) and loginForm.hasClass('visible')
			$('#login-form').hide().removeClass('visible')
		return)

	$('#app-button').click (event)->
		location.pathname = 'demo'
		return

	$('.next-button').click (event)->
		fullpage_api.moveSectionDown()
		return

	$('#submit-form').click (event)->
		event.preventDefault()
		event.stopPropagation()
		# $('#intro-video').empty()

		$('.participate-section').removeClass('hidden').show()
		# $('form .cd-footer').removeClass('hidden').show()
		$('#submit-form').hide()
		
		# $('input[type=radio]').change((event)->
		# 	if $(this).is(':checked')

		# )
		return -1

	$('.cd-radio').click (event)->
		event.preventDefault()
		event.stopPropagation()

		# $('#intro-video').empty()
		# $('form .cd-footer').removeClass('hidden').show()

		$(this).addClass('checked').siblings('.cd-radio').removeClass('checked')
		checkSurveyCompleted()

		if $(this).hasClass('validate')
			$(this).parents('.cd-section').find('.cd-validate').removeClass('hidden').show()
		else
			setTimeout(surveyNext, 500)

		return -1

	$('.cd-radio select').click (event)->
		event.preventDefault()
		event.stopPropagation()
		return -1

	$('.cd-radio select').on('change', (event)->
		event.preventDefault()
		event.stopPropagation()

		$('.cd-radio').removeClass('checked')

		$(this).parents('.cd-radio').addClass('checked').siblings('.cd-radio').removeClass('checked')

		$(this).parents('.cd-section').find('.cd-validate').removeClass('hidden').show()
		return -1)

	$('.cd-checkbox').click (event)->
		event.preventDefault()
		event.stopPropagation()
		$(this).toggleClass('checked')
		checkSurveyCompleted()

		$(this).parents('.cd-section').find('.cd-validate').removeClass('hidden').show()
		return -1

	$('.cd-validate button').click (event)->
		event.preventDefault()
		event.stopPropagation()
		if $(this).hasClass('email')
			
			email = $('#id_email').val()

			toArray = (value)->
				return if value? then [value] else []

			answers = {}
			participate = $('.cd-section.participate').find('.cd-radio.checked').attr('data-value')
			if participate == 'as-soon-as'
				participate = $('.cd-section.participate').find('.cd-radio select').val()
			answers['participate'] = toArray(participate)
			answers['participate-event'] = $('.cd-section.participate-event').find('.cd-checkbox.checked').map( ()-> return $(this).attr('data-value') ).toArray()
			answers['num-drawings'] = toArray($('.cd-section.num-drawings').find('.cd-radio.checked').attr('data-value'))
			answers['print-size'] = toArray($('.cd-section.print-size').find('.cd-radio.checked').attr('data-value'))

			args = 
				email: email
				answers: answers
			$.ajax( method: "POST", url: "ajaxCall/", data: data: JSON.stringify { function: 'submitSurvey', args: args } ).done((result)->
				
				$('#survey-email').hide()
				$('.cd-validate.email').hide()

				
				

				if result.status == 'error'
					if result.message == 'Your email is invalid'
						$('#survey-error').removeClass('hidden').show()
						$('#survey-error p').text("Cette adresse email n'est pas valide.")
					if result.message == 'Some answers are not valid'
						$('#survey-error').removeClass('hidden').show()
						$('#survey-error p').text("Certaines réponses ne sont pas valides.")
				else
					$('#survey-sent').removeClass('hidden').show()
					if result.message == 'Your participation was successfully updated'
						$('#survey-sent h3').text('Votre participation a bien été mise à jour !')

				return)

			return
		surveyNext()
		return -1

	Chart.defaults.global.defaultFontSize = 14

	$.ajax( method: "POST", url: "ajaxCall/", data: data: JSON.stringify { function: 'getSurveyResults', args: {} } ).done((result)->
		
		surveyResultsJ = $('#survey-results')
		
		margins = 300

		n = 0

		for questionObject in result

			canvasJ = $('<canvas>').attr('width', (window.innerWidth / 2 - margins) + 'px').attr('height', (window.innerHeight / 2 - margins) + 'px')

			slideJ = $( surveyResultsJ.find('.chart').get(n) )
			# slideJ = $('<div>').addClass('slide')
			titleJ = $('<h3>').text(questionObject.text)
			slideJ.append(titleJ)
			slideJ.append(canvasJ)
			# surveyResultsJ.append(slideJ)

			chart = new Chart(canvasJ.get(0), {
				type: 'bar',
				data: {
					labels: questionObject.legends,
					datasets: [{
						label: questionObject.text,
						data: questionObject.answers,
						# data: [41, 52, 63, 74, 85, 96, 107, 118, 12, 13, 14],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)',
							'rgba(205, 220, 57, 0.2)'
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)',
							'rgba(205, 220, 57, 1)'
						],
						borderWidth: 1
					}]
				},
				options: { 
					# responsive: false 
					legend: {
						display: false,
						# position: 'bottom'
						# labels: { boxWidth: 0 }
					}
					scales: {
						yAxes: [{
							ticks: {
								stepSize: 1
							},
							display: true,
							scaleLabel: {
								display: true,
								labelString: 'Nombre de votes'
							}
						}]
					}
				}
			})
			n++

		return)
	

	# $('.cd-footer .btn.up').click (event)->
	# 	event.preventDefault()
	# 	event.stopPropagation()
	# 	surveyPrevious()
	# 	return -1

	# $('.cd-footer .btn.down').click (event)->
	# 	event.preventDefault()
	# 	event.stopPropagation()
	# 	surveyNext()
	# 	return -1

	$('#id_email').on("change paste keyup", ()->
		text = $(this).val()
	
		if validateEmail(text)
			$('.cd-validate').removeClass('hidden').show()
		else
			$('.cd-validate').hide()
		return
	)

			
	return