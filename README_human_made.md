# CheckEM: VLM ensemble-based web content analysis

[CheckEM](https://www.checkem.tech/) analyses web pages for suspicious content using an ensemble of VLMs. 

## Motivation

The internet's getting more and more abundant with false information and misleading content. Verifying wheter something can be trusted or not is a problem both for direct human browsers and AI agents or search engines which really decide what information human readers come across.


## How it works

CheckEM is an app that combines the powers of VLMs from various providers to give you the most precise evaluation possible about the whether you can trust a web page or not. 

The app displays a simple list of websites with indicators on their level of suspicion. When you click one, it opens up a high level view telling if each model trusts it or not. From there, you can open the full page content with highlights indicating the pieces of content that any of the models found suspicious. Furthermore, you can click on the highlights to see what each model thinks of that specific piece of content, giving you insight on whether it's actually an indicator of malicious content or not.

If you're not that interested in the details, you can also view a higher level summary of what all the models think, and which types of misleading content they found on the page. 

## Technical details

The system works by first scraping the website and feeding each VLM the full context. All models review the page and flag any content they find suspicious. If any model flags anything, all these specific points are reviewed in detail by all models, providing a precise analysis of all suspicious content. The model reviews are then used to generate an overall consensus on whether the page is trustworthy or not. 

The ensemble system constructed from models of different families is the key to the performance of the method. All models come with their biases and the most reliable results are obtained when opinions from multiple sources are weighed.

The webscraping is done using the Oxylabs API and the web app is hosted on the Hostinger VPS platform with API connections to the Gemma, Nemotron, Gemini, Kimi, and Claude models.