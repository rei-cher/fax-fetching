import json, os, time, asyncio, aiohttp

from .sync_process import process_downloaded_pdfs

async def download_pdf(session, item, headers, output_dir):
    pdf_id = item.get("ID")
    url = f"{headers['base_url']}/{pdf_id}"
    path = os.path.join(output_dir, f"pdf-{pdf_id}.pdf")

    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                with open(path, 'wb') as f:
                    f.write(await resp.read())
                print(f"Downloaded: {pdf_id}")
                return path, item
            else:
                print(f"Failed to download {pdf_id} — Status: {resp.status}")
    except Exception as e:
        print(f"Error downloading {pdf_id}: {e}")
    return None, item

async def download_batch(data, headers, output_dir):
    sem = asyncio.Semaphore(20)
    async with aiohttp.ClientSession() as session:
        tasks = [
            async_download_with_semaphore(sem, session, item, headers, output_dir)
            for item in data
        ]
        return await asyncio.gather(*tasks)

async def async_download_with_semaphore(sem, session, item, headers, output_dir):
    async with sem:
        return await download_pdf(session, item, headers, output_dir)

def fetch_and_analyze_async(url, token, location, path, date, poppler_path, tesseract_path):
    with open(f"{path}/dump-{date}.json", 'r') as file:
        data = json.load(file)["data"]

    headers = {
        "content-type": "application/pdf",
        "Authorization": f"Bearer {token}",
        "Location-id": location,
        "base_url": url
    }

    pdf_dump_dir = os.path.join(path, "pdf_dump")
    os.makedirs(pdf_dump_dir, exist_ok=True)

    batch_size = 20
    all_results = []

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        print(f"\nBatch {i//batch_size + 1} — downloading {len(batch)} PDFs...")

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(download_batch(batch, headers, pdf_dump_dir))
        all_results.extend(results)

        if i + batch_size < len(data):
            time.sleep(1)
       
    process_downloaded_pdfs(all_results, poppler_path, path, tesseract_path=tesseract_path)
