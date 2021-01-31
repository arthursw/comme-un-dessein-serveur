from Wetu import settings

def settings_context_processor(request):
	return { 'application': settings.APPLICATION, 'isCommeUnDessein': settings.APPLICATION == 'COMME_UN_DESSEIN' }