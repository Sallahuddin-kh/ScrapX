import requests
from django.http import HttpResponse
from bs4 import BeautifulSoup
import tempfile
import os
import zipfile
from django.http import FileResponse
from django.shortcuts import render
from urllib.parse import urljoin

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

def scrape_and_download_text(request):
    if request.method == 'POST':
        start_url = request.POST.get('start_url', '')

        try:
            # Create a temporary directory to store the text files
            temp_dir = tempfile.mkdtemp()

            # Send an HTTP GET request to the start URL
            response = requests.get(start_url)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content of the start page using BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract text and headings
                extracted_content = extract_text_and_headings(soup)

                # Create a temporary text file to store the extracted content
                temp_file_path = os.path.join(temp_dir, 'page_1.txt')
                with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(extracted_content)

                # Extract and add all URLs on the start page to the list of URLs to scrape
                visited_urls = set()
                urls_to_scrape = []
                for a_tag in soup.find_all('a', href=True):
                    absolute_url = urljoin(start_url, a_tag['href'])
                    if absolute_url not in visited_urls:
                        urls_to_scrape.append(absolute_url)
                        visited_urls.add(absolute_url)

                # Loop through the first level of linked pages
                for i, url in enumerate(urls_to_scrape):
                    if i == 5:
                        break
                    response = requests.get(url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        extracted_content = extract_text_and_headings(soup)
                        temp_file_path = os.path.join(temp_dir, f'page_{i + 2}.txt')  # Start with 'page_2.txt'
                        with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                            temp_file.write(extracted_content)
                # Create a zip file containing all text files
                zip_file_path = os.path.join(temp_dir, 'text_files.zip')
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

                # Prepare the zip file for download
                with open(zip_file_path, 'rb') as zip_file:
                    response = HttpResponse(zip_file.read(), content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename="text_files.zip"'
                    return response
            else:
                return HttpResponse(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")

    # Render a template with a form to input the starting URL
    return render(request, 'scrape_and_download.html')
