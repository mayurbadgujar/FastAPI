from fastapi import FastAPI,HTTPException, Depends,Security
from fastapi.security import APIKeyHeader
import requests

app= FastAPI()

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != "ApiKey":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

user_wallet = {}

API_URL = "https://api.nbp.pl/api/exchangerates/rates/c/{currency}?format=json"


async def get_exchange_rate(currency:str,api_key: str = Depends(get_api_key))->float:
    try:
        response =requests.get(API_URL.format(currency=currency))
        if response.status_code==200:
            data=response.json()
            return data["rates"][0].get("ask")
        else:
            return None
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500,detail="Error fetching exchange rate")


@app.get("/")
def get():
    print("welcome to CICD pipeline")


@app.get("/wallet")
async def get_wallet(api_key: str = Depends(get_api_key)):
    total_pln=0
    pln_values={}

    for currency, amount in user_wallet.items():
        rate=await get_exchange_rate(currency)
        if rate is None:
            raise HTTPException(status_code=500, detail=f"Failed to fetch exchange rate for {currency}")
        pln_values[currency]=amount*rate
        total_pln +=pln_values[currency]
    
    return {
        "wallet": user_wallet,
        "pln_values": pln_values,
        "total_pln": total_pln
    }


@app.post("/wallet/add/{currency}/{amount}")
async def add_to_wallet(currency:str,amount:float,api_key: str = Depends(get_api_key)):
    if currency in user_wallet:
        user_wallet[currency] +=amount
    else:
        user_wallet[currency] =amount
    return {"message": f"Added {amount} {currency} to the wallet."}


@app.post("/wallet/subtract/{currency}/{amount}")
async def subtract_from_wallet(currency:str,amount:float,api_key: str = Depends(get_api_key)):
    if currency not in user_wallet or user_wallet[currency]<amount:
        raise HTTPException(status_code=400,detail=f"Not enough {currency} in the wallet.")
    user_wallet[currency]-=amount
    return {"message":f"Subtracted {amount} {currency} from the wallet."}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)