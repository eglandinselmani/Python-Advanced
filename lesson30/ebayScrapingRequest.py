import requests

url = "https://gjirafa50.com/search?q=laptop+"



responses =requests.get(url)


if responses.status_code ==200:
    print(responses.text)
else:
    print(f"Failed to retrive content from {url}")