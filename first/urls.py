from django.contrib import admin
from django.urls import path, include
from first import views
app_name = 'first'

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', views.register, name='register'),
    path('userdetails/', views.login_user, name='userdetails'),
    path('event/', views.event, name='event'),
    path('initial_capital', views.initial_capital, name='initial_capital'),
    path('get_log', views.get_log, name='get_log'),
    path('Gethistoric', views.get_historic, name='get_historic'),
    path('Startalgo', views.get_started, name='get_started'),
    path('Stopalgo_s', views.get_started, name='get_started'),
    path('updatemarketwatchstrike', views.updatemarketwatchstrike, name='updatemarketwatchstrike'),
    path('update_maindatabase', views.update_maindatabase, name='update_maindatabase'),
    path('screener_only', views.screener_only, name='screener_only'),
    path('screener_only_topgainer', views.screener_only_topgainer, name='screener_only_topgainer'),
    path('scrip_master_updation', views.scrip_master_updation, name='scrip_master_updation'),
    path('MarketWatch', views.MarketWatch, name='MarketWatch'),
    path('VolumeRatio', views.VolumeRatio, name='VolumeRatio'),
    path('get_stocklistmkt', views.get_stocklistmkt, name='get_stocklistmkt'),
    path('removeStock_maindatabase', views.removeStock_maindatabase, name='removeStock_maindatabase'),
]