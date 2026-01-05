Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      get "health", to: "health#show"
      get "auth/shopify", to: "shopify_auth#start"
      get "auth/shopify/callback", to: "shopify_auth#callback"
    end
  end
end
