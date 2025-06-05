from django.urls import path
from django.contrib.auth import views as auth_views
from gestionale import views

app_name = 'gestionale'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Clienti
    path('clienti/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clienti/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clienti/nuovo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clienti/<int:pk>/modifica/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clienti/<int:pk>/elimina/', views.ClienteDeleteView.as_view(), name='cliente_delete'),

    # Modelli
    path('modelli/', views.ModelloListView.as_view(), name='modello_list'),
    path('modelli/<int:pk>/', views.ModelloDetailView.as_view(), name='modello_detail'),
    path('modelli/nuovo/', views.ModelloCreateView.as_view(), name='modello_create'),
    path('modelli/<int:pk>/modifica/', views.ModelloUpdateView.as_view(), name='modello_update'),
    path('modelli/<int:pk>/elimina/', views.ModelloDeleteView.as_view(), name='modello_delete'),
    path('modelli/<int:pk>/duplica/', views.modello_duplicate, name='modello_duplicate'),

    # Componenti
    path('componenti/', views.ComponenteListView.as_view(), name='componente_list'),
    path('componenti/<int:pk>/', views.ComponenteDetailView.as_view(), name='componente_detail'),
    path('componenti/nuovo/', views.ComponenteCreateView.as_view(), name='componente_create'),
    path('componenti/nuovo/modello/<int:modello_id>/', views.ComponenteCreateView.as_view(), name='componente_create_for_modello'),
    path('componenti/<int:pk>/modifica/', views.ComponenteUpdateView.as_view(), name='componente_update'),
    path('componenti/<int:pk>/elimina/', views.ComponenteDeleteView.as_view(), name='componente_delete'),

    # Colori
    path('colori/', views.ColoreListView.as_view(), name='colore_list'),
    path('colori/<int:pk>/', views.ColoreDetailView.as_view(), name='colore_detail'),
    path('colori/nuovo/', views.ColoreCreateView.as_view(), name='colore_create'),
    path('colori/<int:pk>/modifica/', views.ColoreUpdateView.as_view(), name='colore_update'),
    path('colori/<int:pk>/elimina/', views.ColoreDeleteView.as_view(), name='colore_delete'),

    # Coppie Misure
    path('coppiemisure/', views.CoppiaMisuraListView.as_view(), name='coppiamisura_list'),
    path('coppiemisure/<int:pk>/', views.CoppiaMisuraDetailView.as_view(), name='coppiamisura_detail'),
    path('coppiemisure/nuovo/', views.CoppiaMisuraCreateView.as_view(), name='coppiamisura_create'),
    path('coppiemisure/<int:pk>/modifica/', views.CoppiaMisuraUpdateView.as_view(), name='coppiamisura_update'),
    path('coppiemisure/<int:pk>/elimina/', views.CoppiaMisuraDeleteView.as_view(), name='coppiamisura_delete'),

    # Ordini
    path('ordini/', views.OrdineListView.as_view(), name='ordine_list'),
    path('ordini/<int:pk>/', views.OrdineDetailView.as_view(), name='ordine_detail'),
    path('ordini/nuovo/', views.OrdineCreateView.as_view(), name='ordine_create'),
    path('ordini/nuovo/modello/<int:modello_id>/', views.OrdineCreateView.as_view(), name='ordine_create_for_modello'),
    path('ordini/<int:pk>/modifica/', views.OrdineUpdateView.as_view(), name='ordine_update'),
    path('ordini/<int:pk>/elimina/', views.OrdineDeleteView.as_view(), name='ordine_delete'),
    path('ordini/<int:pk>/conferma/', views.ordine_conferma, name='ordine_conferma'),
    path('ordini/<int:pk>/annulla/', views.ordine_annulla, name='ordine_annulla'),

    # Dettagli Ordine
    path('dettagliordine/nuovo/', views.DettaglioOrdineCreateView.as_view(), name='dettaglioordine_create'),
    path('dettagliordine/nuovo/ordine/<int:ordine_id>/', views.DettaglioOrdineCreateView.as_view(), name='dettaglioordine_create_for_ordine'),
    path('dettagliordine/<int:pk>/modifica/', views.DettaglioOrdineUpdateView.as_view(), name='dettaglioordine_update'),
    path('dettagliordine/<int:pk>/elimina/', views.DettaglioOrdineDeleteView.as_view(), name='dettaglioordine_delete'),

    # Report
    path('report/bolla/<int:pk>/', views.bolla_ordine_pdf, name='bolla_ordine_pdf'),
    path('report/materiali/<int:pk>/', views.scheda_materiali_pdf, name='scheda_materiali_pdf'),
    path('report/modello/<int:pk>/', views.scheda_modello_pdf, name='scheda_modello_pdf'),
     path('report/dashboard/', views.report_dashboard, name='report_dashboard'),

    # Autenticazione
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]
