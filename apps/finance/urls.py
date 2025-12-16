from django.urls import path
from apps.finance import views

urlpatterns = [
    path('factures/', views.FactureListView.as_view(), name='facture-list'),
    path('factures/create/', views.FactureCreateView.as_view(), name='facture-create'),
    path('factures/<int:facture_id>/details/', views.FactureDetailView.as_view(), name='facture-detail'),
    path('factures/<int:facture_id>/update/', views.FactureUpdateView.as_view(), name='facture-update'),
    path('factures/<int:facture_id>/delete/', views.FactureDeleteView.as_view(), name='facture-delete'),
]
