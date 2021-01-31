from django.conf.urls import include, url
from draw import views
import socketio.sdjango

socketio.sdjango.autodiscover()

urlpatterns = [

    url(r'^$', views.welcome, name='welcome'),
    url(r'^ajaxCall/$', views.ajaxCall),
    url(r'^connexion/ajaxCall/$', views.ajaxCall),
    url(r'^live/$', views.live),
    url(r'^email/desactivation/$', views.disableEmail, {'activation': False}),
    url(r'^email/reactivation/$', views.disableEmail, {'activation': True}),
    url(r'^ajaxCallNoCSRF/$', views.ajaxCallNoCSRF),
    
    url(r'^draw/templates/index\.html', views.index, name='index'),
    url(r'^draw/index\.html', views.index, name='index'),
    url(r'^index\.html', views.index, name='index'),
    url(r'^drawing-(?P<pk>[\w]+)$', views.index, {'visit': True}, name='index'),
    url(r'^debug/drawing-(?P<pk>[\w]+)$', views.index, {'visit': True, 'useDebugFiles': True}, name='index'),
    url(r'^tile-(?P<tilePk>[\w]+)$', views.index, {'visit': True}, name='index'),
    url(r'^debug/tile-(?P<tilePk>[\w]+)$', views.index, {'visit': True, 'useDebugFiles': True}, name='index'),
    # url(r'^connexion/$', views.connection, name='connection'),
    # url(r'^connexions/$', views.connections, name='connections'),
    url(r'^visite', views.index, {'visit': True}, name='index'),
    url(r'^debug-visite', views.index, {'visit': True, 'useDebugFiles': True}, name='index'),
    url(r'^about\.html', views.about),
    url(r'^privacy-policy\.html', views.privacyPolicy),
    url(r'^terms-of-service\.html', views.termsOfService),
    
    url(r'^(?P<cityName>(?!admin)[\w-]+)/$', views.index, {'visit': True}, name='index'),
    url(r'^(?P<cityName>(?!admin)[\w-]+)/drawing-(?P<pk>[\w]+)$', views.index, {'visit': True}, name='index'),
    url(r'^(?P<cityName>(?!admin)[\w-]+)/tile-(?P<tilePk>[\w]+)$', views.index, {'visit': True}, name='index'),
    url(r'^debug/(?P<cityName>(?!admin)[\w-]+)/$', views.index, { 'useDebugFiles': True }, name='index'),
    url(r'^debug/(?P<cityName>(?!admin)[\w-]+)/drawing-(?P<pk>[\w]+)$', views.index, { 'useDebugFiles': True }, name='index'),
    url(r'^debug/(?P<cityName>(?!admin)[\w-]+)/tile-(?P<tilePk>[\w]+)$', views.index, { 'useDebugFiles': True }, name='index'),

    url(r'^debug-free$', views.index, {'drawingMode': 'free', 'useDebugFiles': True}, name='index'),
    url(r'^debug-pixel$', views.index, {'drawingMode': 'pixel', 'useDebugFiles': True}, name='index'),
    url(r'^debug-image$', views.index, {'drawingMode': 'image', 'useDebugFiles': True}, name='index'),
    url(r'^debug-ortho$', views.index, {'drawingMode': 'ortho', 'useDebugFiles': True}, name='index'),
    url(r'^debug-ortho-diag$', views.index, {'drawingMode': 'orthoDiag', 'useDebugFiles': True}, name='index'),
    url(r'^debug-line-ortho-diag$', views.index, {'drawingMode': 'lineOrthoDiag', 'useDebugFiles': True}, name='index'),
    url(r'^debug-line$', views.index, {'drawingMode': 'line', 'useDebugFiles': True}, name='index'),
    url(r'^debug-pen$', views.index, {'drawingMode': 'pen', 'useDebugFiles': True}, name='index'),
    
    url(r'^free$', views.index, {'drawingMode': 'free'}, name='index'),
    url(r'^pixel$', views.index, {'drawingMode': 'pixel'}, name='index'),
    url(r'^image$', views.index, {'drawingMode': 'image'}, name='index'),
    url(r'^ortho$', views.index, {'drawingMode': 'ortho'}, name='index'),
    url(r'^ortho-diag$', views.index, {'drawingMode': 'orthoDiag'}, name='index'),
    url(r'^line-ortho-diag$', views.index, {'drawingMode': 'lineOrthoDiag'}, name='index'),
    url(r'^line$', views.index, {'drawingMode': 'line'}, name='index'),
    url(r'^pen$', views.index, {'drawingMode': 'pen'}, name='index'),

    # url(r'^#(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$', views.index, name='index'),
    # url(r'^(?P<owner>[\w-]+)/(?P<name>[\w-]+)/#(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$', views.index, name='index'),
    # url(r'^#(?P<x>[\d.]+),(?P<y>[\d.]+)$', views.index, name='index'),
    # url(r'^#(?P<owner>[\w]+)/(?P<city>[\w-]+)$', views.index, name='index'),
    # url(r'^#(?P<owner>[\w]+)/(?P<city>[\w-]+)/(?P<x>[\d.]+),(?P<y>[\d.]+)$', views.index, name='index'),
    # url(r'^#sites/(?P<site>[\w]+)$', views.index, name='index'),
    # url(r'^#sites/(?P<site>[\w]+)/(?P<x>[\d.]+),(?P<y>[\d.]+)$', views.index, name='index'),
    # url(r'^#(?P<owner>[\w]+)/(?P<city>[\w-]+)/sites/(?P<site>[\w]+)$', views.index, name='index'),
    # url(r'^#(?P<owner>[\w]+)/(?P<city>[\w-]+)/sites/(?P<site>[\w]+)/(?P<x>[\d.]+),(?P<y>[\d.]+)$', views.index, name='index'),
    # url(r'^rasterizer/$', views.index),
    # url(r'^rasterizer/ajaxCall/$', views.ajaxCall),
    # url(r'^rasterizer/#(?P<x>[\d.]+),(?P<y>[\d.]+)$', views.index),
    # url(r'^rasterizer/#(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$', views.rasterizer, name='index'),
    # url(r'^([\w,.,-]+)$', views.index, name='index'),
    # url(r'^(?P<sitename>([\w,.,-]+)).romanesc.co/', views.index, name='index'),

    url(r"^socket\.io", include(socketio.sdjango.urls)),
]
