from django.contrib import admin
from django.urls import path, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Importa le viste direttamente dalla tua app 'gestionale'
from gestionale import views

# Non definire 'app_name' in questo file
# app_name = 'gestionale' # RIMUOVI QUESTA RIGA

urlpatterns = [
    # URL per l'interfaccia di amministrazione
    path('admin/', admin.site.urls),

    # Home
    path('', views.home, name='home'),

    # Clienti
    path('clienti/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clienti/nuovo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clienti/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clienti/<int:pk>/modifica/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clienti/<int:pk>/elimina/', views.ClienteDeleteView.as_view(), name='cliente_delete'),

    # Modelli
    path('modelli/', views.ModelloListView.as_view(), name='modello_list'),
    path('modelli/nuovo/', views.ModelloCreateView.as_view(), name='modello_create'),
    path('modelli/<int:pk>/', views.ModelloDetailView.as_view(), name='modello_detail'),
    path('modelli/<int:pk>/modifica/', views.ModelloUpdateView.as_view(), name='modello_update'),
    path('modelli/<int:pk>/elimina/', views.ModelloDeleteView.as_view(), name='modello_delete'),
    path('modelli/<int:pk>/duplica/', views.modello_duplicate, name='modello_duplicate'),

    # Tipi Componente
    path('tipicomponente/', views.TipoComponenteListView.as_view(), name='tipocomponente_list'),
    path('tipicomponente/nuovo/', views.TipoComponenteCreateView.as_view(), name='tipocomponente_create'),
    path('tipicomponente/<int:pk>/', views.TipoComponenteDetailView.as_view(), name='tipocomponente_detail'),
    path('tipicomponente/<int:pk>/modifica/', views.TipoComponenteUpdateView.as_view(), name='tipocomponente_update'),
    path('tipicomponente/<int:pk>/elimina/', views.TipoComponenteDeleteView.as_view(), name='tipocomponente_delete'),

    # Componenti e Articoli (Misure Specifiche)
    path('componenti/nuovo/', views.ComponenteCreateView.as_view(), name='componente_create'),
    path('modelli/<int:modello_id>/componenti/nuovo/', views.ComponenteCreateView.as_view(), name='componente_create_for_modello'),
    path('componenti/<int:pk>/modifica/', views.ComponenteUpdateView.as_view(), name='componente_update'),
    path('componenti/<int:pk>/elimina/', views.ComponenteDeleteView.as_view(), name='componente_delete'),
    path('componenti/<int:componente_id>/misure/', views.manage_articoli_componente, name='manage_articoli_componente'),

    # Colori
    path('colori/', views.ColoreListView.as_view(), name='colore_list'),
    path('colori/nuovo/', views.ColoreCreateView.as_view(), name='colore_create'),
    path('colori/<int:pk>/', views.ColoreDetailView.as_view(), name='colore_detail'),
    path('colori/<int:pk>/modifica/', views.ColoreUpdateView.as_view(), name='colore_update'),
    path('colori/<int:pk>/elimina/', views.ColoreDeleteView.as_view(), name='colore_delete'),

    # Taglie
    path('taglie/', views.TagliaListView.as_view(), name='taglia_list'),
    path('taglie/nuova/', views.TagliaCreateView.as_view(), name='taglia_create'),
    path('taglie/<int:pk>/', views.TagliaDetailView.as_view(), name='taglia_detail'),
    path('taglie/<int:pk>/modifica/', views.TagliaUpdateView.as_view(), name='taglia_update'),
    path('taglie/<int:pk>/elimina/', views.TagliaDeleteView.as_view(), name='taglia_delete'),

    # Ordini
    path('ordini/', views.OrdineListView.as_view(), name='ordine_list'),
    path('ordini/nuovo/', views.OrdineCreateView.as_view(), name='ordine_create'),
    path('modelli/<int:modello_id>/ordini/nuovo/', views.OrdineCreateView.as_view(), name='ordine_create_for_modello'),
    path('ordini/<int:pk>/', views.OrdineDetailView.as_view(), name='ordine_detail'),
    path('ordini/<int:pk>/modifica/', views.OrdineUpdateView.as_view(), name='ordine_update'),
    path('ordini/<int:pk>/elimina/', views.OrdineDeleteView.as_view(), name='ordine_delete'),
    path('ordini/<int:pk>/conferma/', views.ordine_conferma, name='ordine_conferma'),
    path('ordini/<int:pk>/annulla/', views.ordine_annulla, name='ordine_annulla'),

    # Dettagli Ordine
    path('ordini/<int:ordine_id>/dettagli/nuovo/', views.DettaglioOrdineCreateView.as_view(), name='dettaglioordine_create_for_ordine'),
    path('dettagliordine/<int:pk>/modifica/', views.DettaglioOrdineUpdateView.as_view(), name='dettaglioordine_update'),
    path('dettagliordine/<int:pk>/elimina/', views.DettaglioOrdineDeleteView.as_view(), name='dettaglioordine_delete'),

    # Report
    path('report/bolla/<int:pk>/', views.bolla_ordine_pdf, name='bolla_ordine_pdf'),
    path('report/materiali/<int:pk>/', views.scheda_materiali_pdf, name='scheda_materiali_pdf'),
    path('report/modello/<int:pk>/', views.scheda_modello_pdf, name='scheda_modello_pdf'),
    path('report/dashboard/', views.report_dashboard, name='report_dashboard'),

    # Autenticazione
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url=reverse_lazy('password_change_done')
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

# Aggiungi questo per servire i file media in modalità DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)