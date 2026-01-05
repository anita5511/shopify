require 'rails_helper'

RSpec.describe "Api::V1::Questions", type: :request do
  let!(:shop) { Shop.create!(shop_domain: 'test-store.myshopify.com', access_token: 'test_token', shop_name: 'Test Store') }
  
  describe "POST /api/v1/questions" do
    context "with valid parameters" do
      let(:valid_params) do
        {
          store_id: 'test-store.myshopify.com',
          question: 'What were my sales last week?'
        }
      end
      
      before do
        # Mock the Python AI client
        allow_any_instance_of(PythonAiClient).to receive(:query).and_return({
          success: true,
          data: {
            answer: "Test answer",
            confidence: "high",
            shopifyql: "SELECT * FROM orders",
            intent: "sales",
            used_data_sources: ["orders"]
          }
        })
      end
      
      it "returns a successful response" do
        post "/api/v1/questions", params: valid_params
        
        expect(response).to have_http_status(:success)
        json = JSON.parse(response.body)
        expect(json['answer']).to eq('Test answer')
        expect(json['confidence']).to eq('high')
      end
    end
    
    context "with missing store_id" do
      it "returns a bad request error" do
        post "/api/v1/questions", params: { question: 'Test question' }
        
        expect(response).to have_http_status(:bad_request)
        json = JSON.parse(response.body)
        expect(json['error']).to include('store_id')
      end
    end
    
    context "with missing question" do
      it "returns a bad request error" do
        post "/api/v1/questions", params: { store_id: 'test-store.myshopify.com' }
        
        expect(response).to have_http_status(:bad_request)
        json = JSON.parse(response.body)
        expect(json['error']).to include('question')
      end
    end
    
    context "with non-existent store" do
      it "returns a not found error" do
        post "/api/v1/questions", params: {
          store_id: 'nonexistent-store.myshopify.com',
          question: 'Test question'
        }
        
        expect(response).to have_http_status(:not_found)
        json = JSON.parse(response.body)
        expect(json['error']).to include('not found')
      end
    end
  end
end
