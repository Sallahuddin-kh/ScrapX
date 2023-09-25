import requests
from django.http import HttpResponse
from bs4 import BeautifulSoup
import tempfile
import os
from django.http import FileResponse
from django.shortcuts import render

def extract_text_and_headings(soup):
    # Extract visible text and headings from the HTML content
    text_and_headings = []
    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text_and_headings.append(element.get_text())
    return "\n".join(text_and_headings)

def scrape_and_download_html(request):
    if request.method == 'POST':
        url = request.POST.get('url', '')

        try:
            # Send an HTTP GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content of the page using BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract text and headings
                extracted_content = extract_text_and_headings(soup)

                # Create a temporary file to store the extracted content
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
                    tmp_file.write(extracted_content.encode('utf-8'))
                    tmp_file_path = tmp_file.name

                # Prepare the file for download
                with open(tmp_file_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type='text/plain')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(tmp_file_path)}"'
                    return response
            else:
                return HttpResponse(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")

    # Render a template with a form to input the URL
    return render(request, 'scrape_and_download.html')
