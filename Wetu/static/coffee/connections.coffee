
$(document).ready () ->
	$('#google-button').click (e)=>
		localStorage.setItem('just-logged-in', 'true')
		return
	$('#facebook-button').click (e)=>
		localStorage.setItem('just-logged-in', 'true')
		return
	return