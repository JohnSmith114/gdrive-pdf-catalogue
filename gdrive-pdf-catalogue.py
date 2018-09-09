from apiclient import http
from oauth2client import file, client, tools
from googleapiclient.discovery import build
from httplib2 import Http

from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

'''
	GDrive PDF Catalogue by Kien Tuong Truong
	
	I know this code looks completely botched together (that's because it is!), but it was never meant to be something that could be used by anyone else except me

	This script requires:
		> reportlab
		> the Google Drive API
		> The credentials (credentials.json) from the Google Drive API (in the same folder of this script)
		> A file with the 3 folder IDs (Also in the same folder)
		> The two open source fonts "Oswald-Regular.ttf" and "Roboto-Thin.ttf"
'''

credentialsFile = "credentials.json"
IdFileName = "idfile.txt"

catalogue = SimpleDocTemplate("Library of Babel Catalogue.pdf", pagesize = A4)

pdfmetrics.registerFont(TTFont('Oswald', 'Oswald-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Roboto', 'Roboto-Thin.ttf'))

SCOPES = "https://www.googleapis.com/auth/drive.metadata.readonly"

width, heigth = A4
parts = []

def getIDs(fileName):
	IDFile = open(fileName, "r")
	if IDFile.mode == "r":
		rootId = IDFile.readline().rstrip("\r\n")
		ENG_Id = IDFile.readline().rstrip("\r\n")
		ITA_Id = IDFile.readline().rstrip("\r\n")
	return (rootId, ENG_Id, ITA_Id)

def auth():
	#Opens the browser to authorize and receive the token.json
	store = file.Storage('token.json')
    	creds = store.get()
   	if not creds or creds.invalid:
        	flow = client.flow_from_clientsecrets(credentialsFile, SCOPES)
        	creds = tools.run_flow(flow, store)
	return creds

def getContents(service, folder_ID, depth):
	#Recursively prints all contents of the folder
	page_token = None
	global parts
	
	folderStyle = ParagraphStyle(
		name="Folder",
		fontName="Oswald",
		fontSize=12,
		leftIndent = 30*depth
	)

	itemStyle = ParagraphStyle(
		name="Item",
		fontName="Roboto",
		fontsize=4,
		leftIndent = 30*depth
	)

	while True: 
		param = {}  
		if page_token:
			param['pageToken'] = page_token
		children = service.files().list(q="\'"+folder_ID+"\' in parents", orderBy="name", fields="nextPageToken, files(id, name)", **param).execute()
		for child in children['files']:
			print("  " * depth + child['name'])
			if child['name'].endswith(".pdf") or child['name'].endswith(".epub"):
				#Add here other file extensions if needed
				print("  "*depth+"This is a .pdf")
				parts.append(Paragraph("> "+child['name'], style = itemStyle))
			else:
				print("  "*depth+"This is a folder, searching recursively...")
				parts.append(Spacer(1, 0.1*inch))
				parts.append(Paragraph(child['name'], style = folderStyle))
				parts.append(Spacer(1, 0.1*inch))
				getContents(service, child['id'], depth+1)
		page_token = children.get('nextPageToken')
		if not page_token:
			break

def main():
	
	global parts
	
	titleStyle = ParagraphStyle(
		name="Title",
		fontName="Oswald",
		fontSize=20,
		alignment=TA_CENTER
	)

	subtitleStyle = ParagraphStyle(
		name="Subtitle",
		fontName="Oswald",
		fontSize=10,
		textColor="gray",
		alignment=TA_CENTER
	)
	
	sectionStyle = ParagraphStyle(
		name="Section",
		fontName="Oswald",
		fontSize=15
	)
	
	IDList = getIDs(IdFileName)
	parts.append(Paragraph("Library of Babel", style = titleStyle))
	parts.append(Spacer(1, 0.1*inch))
	parts.append(Paragraph("Knowledge is Power.", style = subtitleStyle))
	parts.append(Spacer(1, 0.2*inch))
	creds = auth()
	service = build('drive', 'v3', http=creds.authorize(Http()))
	parts.append(Paragraph("English Catalogue", sectionStyle))
	parts.append(Spacer(1, 0.2*inch))
	getContents(service, IDList[1], 0)
	parts.append(Spacer(1, 0.2*inch))
	parts.append(Paragraph("Catalogo Italiano", sectionStyle))
	getContents(service, IDList[2], 0)
	catalogue.build(parts)


if __name__ == '__main__':
	main()
