import xmltodict
import json
import translators as ts
import re
import glob
import os
import PySimpleGUI as sg

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def loadSettings():
    global settings
    global sourceLang
    global targetLang
    global DataSetRoot
    global DataSetRootTrad
    if not os.path.isfile("settings.json"):
        settings = 0
        setup()
    try:
        jsonFile = open("settings.json")
        settings = json.load(jsonFile)
        sourceLang = settings['sourceLang']
        targetLang = settings['targetLang']
        DataSetRoot = settings['DataSetRoot']
        DataSetRootTrad = DataSetRoot+'_'+targetLang.upper()
        jsonFile.close()
    except:
        jsonFile.close()
        os.remove("settings.json")
        system.exit("Error: (propably) Corrupted ini file, please try again!")

def setup():
    val={'sourceLang': 'en', 'targetLang': 'fr', 'DataSetRoot': './DataSet_Full DataSet', 'Browser': '/usr/bin/chromium-browser', 'Driver': '/usr/bin/chromedriver', 'translators': {'bing': False, 'google': True, 'deepl': False}}
    if type(settings) is dict:
        val=settings
    lang = ['DE', 'EN', 'FR', 'ES', 'PT', 'IT', 'NL', 'PL', 'RU', 'JA', 'ZH']
    layout = [[sg.Text('DataSet', font=('Raleway', 12), justification='center', auto_size_text=True)],
              [sg.HorizontalSeparator(pad=(0,(0,10)))],
              [sg.Text('DataSet Folder', font=('Raleway', 11)),sg.Input(val['DataSetRoot'],key='DataSetRoot'), sg.FolderBrowse(target='DataSetRoot')],
              [sg.Text('Source Language', font=('Raleway', 11)),sg.Combo(lang,default_value=val['sourceLang'].upper(), size=(10, 10), key='sourceLang'),sg.Text('Target Language', font=('Raleway', 11)),sg.Combo(lang,default_value=val['targetLang'].upper(), size=(10, 10), key='targetLang')],
              [sg.Text('Translators', font=('Raleway', 12), justification='center', auto_size_text=True,pad=(0,(20,0)))],
              [sg.HorizontalSeparator(pad=(0,(0,10)))],
              [sg.Checkbox('Google Translate', default=val['translators']['google'], key='google', font=('Raleway', 11))],
              [sg.Checkbox('Bing Translate', default=val['translators']['bing'], key='bing', font=('Raleway', 11))],
              [sg.Checkbox('Deepl Translate (Slower but better)', default=val['translators']['deepl'], key='deepl', font=('Raleway', 11))],
              [sg.Text('*** Only for Deepl translation ***', font=('Raleway', 12), pad=(0,(20,0)), justification='center', auto_size_text=True)],
              [sg.Text('Browser Folder', font=('Raleway', 11)),sg.Input(val['Browser'],key='Browser'), sg.FolderBrowse(target='-BROWSER FOLDER-')],
              [sg.Text('Browser Driver Folder', font=('Raleway', 11)),sg.Input(val['Driver'],key='Driver', size=(39,2)), sg.FolderBrowse(target='-BROWSER DRIVER FOLDER-')],
              [sg.Button('Back', pad=(0,(25,10)),font=('Raleway', 12)), sg.Button('Save', pad=((390,0),(25,10)),font=('Raleway', 12))]]
    window = sg.Window('Settings', layout)
    while True:  # Event Loop
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Back'):
            break
        if event in ('Save'):
            ini = {
            'sourceLang':values['sourceLang'].lower(),
            'targetLang':values['targetLang'].lower(),
            'DataSetRoot':values['DataSetRoot'],
            'Browser': values['Browser'],
            'Driver': values['Driver'],
            'translators':{'bing':values['bing'],'google':values['google'],'deepl':values['deepl']}}
            with open('settings.json', 'w', encoding="utf-8") as f:
                json.dump(ini, f)
            f.close()
            break
    window.close()
    main()

def loadGlossary(targetLang):
    with open('glossary.json', encoding="utf-8") as json_file:
        load = json.load(json_file)
    if targetLang in load:
        return load[targetLang]
    choice = sg.PopupYesNo('Would you like to built one ?\n\nThis will offer a better translation. Use officials books or character sheet side by side to found the correct translation',title='No Glossary found for target language')
    if choice.lower() == 'yes':
        editGlossary(targetLang)
    else:
        return load['en']

def editGlossary(targetLang):
    with open('glossary.json', encoding="utf-8") as json_file:
        load = json.load(json_file)
        total = len(load['en'])
        if targetLang not in load:
            load[targetLang] = {}
        words = []
        edit = []
        for pos, item in enumerate(load['en']):
            default=''
            if item in load[targetLang]:
                default = load[targetLang][item]
            words.append([sg.Text(item+' : ',font=('Raleway', 16))])
            edit.append([sg.Input(default,size=(50,50),key=item,font=('Raleway', 16))])
        editzone = [[sg.Column(words, vertical_alignment='top',element_justification='right',pad=(10,5)),sg.Column(edit,vertical_alignment='top',element_justification='left',pad=((5,10),5))]]
        buttonLayout = [[sg.Button('Save', pad=(10,(0,25)), button_color=['blue','green'],font=('Raleway', 12))],[sg.Button('Back', pad=(10,(0,25)),font=('Raleway', 12))]]
        layout= [[sg.Column(editzone,size=(1200,700),vertical_scroll_only=True,scrollable=True,vertical_alignment='top',element_justification='left'),sg.VerticalSeparator(),sg.Column(buttonLayout,vertical_alignment='top',element_justification='left')]]
        window = sg.Window('Glossary', layout)
        while True:  # Event Loop
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Back'):
                break  
            if event in ('Save'):
                load[targetLang]=values
                print(json.dumps(load), file=open('glossary.json', 'w', encoding="utf-8"))
                break
        window.close()
        main()

def getPathXml(window):
    if len(window.Element('path').SelectedRows):
        selected_row = window['path'].SelectedRows[0]
        return window['path'].TreeData.tree_dict[selected_row].values
    return ''

def main():
    global Glossary
    loadSettings()
    Glossary = loadGlossary(targetLang)
    if not os.path.exists(DataSetRootTrad):
        os.mkdir(DataSetRootTrad)
    listDir = glob.glob(DataSetRoot+"/**/", recursive=True)
    for key, Dir in enumerate(listDir):
        listDir[key] = Dir.replace('\\','/')
    listDir.remove(DataSetRoot+'/')
    listDir.remove(DataSetRoot+'/EquipmentImages/')
    listDir.sort()
    xmlFiles=sg.TreeData()
    for Dir in listDir:
        trad=str(int((len(glob.glob(DataSetRootTrad+Dir[len(DataSetRoot):]+"*.xml"))/len(glob.glob(Dir+"*.xml")))*100))+'%'
        xmlFiles.insert('',Dir[len(DataSetRoot)+1:][:-1],'[ '+Dir[len(DataSetRoot)+1:][:-1]+' ]',[Dir,trad])
        listFileXML(Dir, xmlFiles)
    listFileXML(DataSetRoot+'/', xmlFiles)
    listLayout = [[sg.Tree(data=xmlFiles, headings=['Path', 'Trad'], font=('Raleway', 12),enable_events=True,visible_column_map=[False,True], col0_width=50, num_rows=38, row_height=20, key='path', show_expanded=False)]]
    buttonLayout = [[sg.Button('Open', pad=(10,(0,25)),bind_return_key=True, button_color=['white','green'],font=('Raleway', 12))],[sg.Button('Edit Glossary', button_color=['white','orange'],pad=(10,(0,570)),font=('Raleway', 12))],[sg.Button('Settings', pad=(10,(0,25)),font=('Raleway', 12))],[sg.Button('Exit', pad=(10,(0,25)),font=('Raleway', 12))]]
    layout= [[sg.Column(listLayout),sg.VerticalSeparator(),sg.Column(buttonLayout,vertical_alignment='top',element_justification='left')]]
    window = sg.Window('OggDude Translate DataSet', layout)
    dblClick = ''
    while True:  # Event Loop
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            quit()  
        if event in ('path','Open'):
            if len(getPathXml(window)) > 2:
                if values['path'] == dblClick:
                    window.close()
                    xmlFile = getPathXml(window)
                    openXML(xmlFile[0],xmlFile[2])
                    break
                dblClick = values['path']
        if event in ('Settings'):
            window.close()
            setup()
            break
        if event in ('Edit Glossary'):
            window.close()
            editGlossary(targetLang)
            break
    main()

def listFileXML(path, obj):
    listXml = glob.glob(path+"*.xml")
    for key, Xml in enumerate(listXml):
        listXml[key] = Xml.replace('\\','/')
    listXml.sort()
    for Xml in listXml:
        progress = 0
        trad = '0%'
        parent=''
        if (len(Xml.split('/')) > 4):
            name = list(Xml.split('/'))[-1][:-4]
            parent = list(Xml.split('/'))[-2]
        else:
            name = list(Xml.split('/'))[-1][:-4]
        if os.path.exists(DataSetRootTrad+Xml[len(DataSetRoot):]):
            trad = '100%'
        else:
            XmlProgress = glob.glob(DataSetRootTrad+Xml[len(DataSetRoot):][:-4]+'*.inprogress')
            if XmlProgress:
                percent = int((int(XmlProgress[0][6:].split('.')[1])/int(XmlProgress[0][6:].split('.')[2]))*100)
                progress = int(XmlProgress[0][6:].split('.')[1])
                trad = str(percent)+'%'
        obj.insert(parent,name,name,[Xml,trad,progress])

def openXML(filePath, progress = 0):
    fileName = filePath[len(DataSetRoot):][:-4]
    global doc
    if progress != 0:
        tempFile = list(glob.glob(DataSetRootTrad+fileName+'*.inprogress'))[0]
        with open(tempFile, encoding="utf-8") as fd:
            doc = xmltodict.parse(fd.read())
    else:
        with open(filePath, encoding="utf-8") as fd:
            doc = xmltodict.parse(fd.read())
            progress = 0
    masterKey = list(doc.keys())[0]
    if (len(filePath.split('/')) > 4):
        if not os.path.exists(DataSetRootTrad+'/'+list(filePath.split('/'))[-2]):
            os.mkdir(DataSetRootTrad+'/'+list(filePath.split('/'))[-2])
        displayOriginal(doc, fileName, progress)   
    else:
        displayOriginal(doc[masterKey], fileName, progress)
    print(xmltodict.unparse(doc, pretty=True), file=open(DataSetRootTrad+fileName+'.xml', 'w', encoding="utf-8"))
    main()

def displayOriginal(items, fileName, progress):
    subKey = list(items.keys())[-1]
    name = subKey
    if 'Key' in items[subKey]:
        name = name + ' - '+items[subKey]['Name']
        items[subKey] =[items[subKey]]
    total = len(items[subKey])
    for pos, item in enumerate(items[subKey][progress:], start=progress):
        sourceLayout = []
        editzoneLayout = []
        for source in getSources(item):
            sourceLayout.append([sg.Text(source,pad=(20,10),font=('Raleway', 12,'italic'))])
        for frame in getNameDesc(item):
            editzoneLayout.append(frame)
        if 'Abbrev' in item:
            Abbrev = sg.InputText(default_text=item['Abbrev'],key='Abbrev', size=(4,1),metadata=['Abbrev',item])
            editzoneLayout.insert(1,[sg.Frame('Abbrev: ',[[sg.Text(item['Abbrev'],font=('Raleway', 12,'italic')),Abbrev]],font=('Raleway', 12,'bold'))])
        if 'BaseMods' in item:
            if 'MiscDesc' in item['BaseMods']['Mod']:
                item['BaseMods']['Mod'] = [item['BaseMods']['Mod']]
            modsTab=[]
            for subItem in item['BaseMods']['Mod']:
                if 'MiscDesc' in subItem:
                    Mod = sg.Multiline(default_text=subItem['MiscDesc'],key='MiscDesc', metadata=['MiscDesc',subItem],size=(59,4),pad=(10,10))
                    modsTab.append([sg.Tab('Mod',[[sg.Frame('Description: ',[[sg.Multiline(default_text=subItem['MiscDesc'],text_color=sg.LOOK_AND_FEEL_TABLE[sg.theme()]['TEXT'],background_color=sg.LOOK_AND_FEEL_TABLE[sg.theme()]['BACKGROUND'],border_width=0,font=('Raleway', 12,'italic'),disabled=True,size=(59,6),pad=(10,10),key='Display_'), sg.Column([[Mod],[sg.Button('Trad',key='Trad_Description',metadata=Mod)]],element_justification='center')]],font=('Raleway', 12,'bold')) ]])])
            editzoneLayout.append([sg.Frame('Mods',[[sg.TabGroup(modsTab,key='Display_')]],font=('Raleway', 12,'bold'))])
        optionsParseXML(item,editzoneLayout)
        if 'SubSpeciesList' in item:
            speciesLayout = []
            if 'SubSpecies' in item['SubSpeciesList']:
                if 'Key' in item['SubSpeciesList']['SubSpecies']:
                    item['SubSpeciesList']['SubSpecies'] = [item['SubSpeciesList']['SubSpecies']]
                for subItem in item['SubSpeciesList']['SubSpecies']:
                    # getNameDesc(subItem)
                    # optionsParseXML(subItem)
                    bloc = []
                    for frame in getNameDesc(subItem):
                        bloc.append(frame)
                    optionsParseXML(subItem,bloc)
                    speciesLayout.append([sg.Tab('Sub Species : '+subItem['Name'],bloc)])
                speciesLayout.insert(0,[sg.Tab('Species',editzoneLayout)])
                editzoneLayout = [[sg.TabGroup(speciesLayout,key='Display_')]]
        frameLayout = [
                          [sg.Frame('Type',[[sg.Text(name,pad=(20,10),font=('Raleway', 12))]],pad=((16,0),0),font=('Raleway', 12,'bold')),sg.Frame('Source:',sourceLayout,pad=(14,0),font=('Raleway', 12,'bold'),key='sources'),sg.Frame('Progress: '+str(pos)+' of '+str(total),[[sg.ProgressBar(total,orientation='horizontal', size=(50,20), pad=(20,10),key='progbar')]],font=('Raleway', 12,'bold'))],
                          [sg.Column([[sg.Column(editzoneLayout)]],size=(1350,800),vertical_alignment='top',vertical_scroll_only=True,scrollable=True,)]
                         ]
        buttonLayout = [[sg.Button('Next', pad=(10,(0,25)), button_color=['white','green'],font=('Raleway', 12), key='valid')],[sg.Button('Back', pad=(10,(0,25)),font=('Raleway', 12))]]
        layout= [[sg.Column(frameLayout),sg.VerticalSeparator(),sg.Column(buttonLayout,vertical_alignment='top',element_justification='left')]]
        window_edit = sg.Window('Edit Item : '+name, layout,size=(1920,1080),font=('Raleway', 12),finalize=True)
        window_trad = ''
        window_edit['progbar'].update(pos)
        if pos+1 == total:
            window_edit['valid'].update('Save')
        if pos > 0 :
            # Save Temp File
            tempFile = DataSetRootTrad+fileName+'.'+str(pos)+'.'+str(total)+'.inprogress'
            print(xmltodict.unparse(doc, pretty=True), file=open(tempFile, 'w', encoding="utf-8"))
        while True:  # Event Loop
            window, event, values = sg.read_all_windows()
            if window == window_edit:
                if event in (sg.WIN_CLOSED, 'Back'):
                    window.close()
                    main()
                if event in ('valid'):
                    for key in values.keys():
                        if re.search('Display_*', key, re.IGNORECASE) is None:
                            elemKey=window[key].metadata[0]
                            elem=window[key].metadata[1]
                            elem[elemKey]=values[key]
                            window.close()
                            window_edit = None

                    break
                if re.search('Trad_*', event, re.IGNORECASE):
                    elem=window[event].metadata
                    trads = tradChoice(elem.Get())
                    if (len(trads)>1):
                        tradItems =[]
                        tradLayout =[]
                        for trad in trads:
                            tradItems.append([sg.Column([[sg.Multiline(default_text=trad,size=(30,18),text_color=sg.LOOK_AND_FEEL_TABLE[sg.theme()]['TEXT'],background_color=sg.LOOK_AND_FEEL_TABLE[sg.theme()]['BACKGROUND'],border_width=0,font=('Raleway', 12,'italic'),disabled=True,pad=(10,10),key='Txt_Trad')], [sg.Button('Select',metadata=trad)]],element_justification='center'), sg.VerticalSeparator()])
                        tradItems.append([sg.Button('Back')])
                        for tradItem in tradItems:
                            tradLayout.append(sg.Column([tradItem]))
                        window_trad = sg.Window('Chose translate',[tradLayout],size=(1400,500),finalize=True)
                    else:
                        elem.Update(trads[0])
            if window == window_trad:
                if event in (sg.WIN_CLOSED, 'Back'):
                    window.close()
                    window_trad = None
                else:
                    elem.Update(window[event].metadata)
                    window.close()
                    window_trad = None
        if pos > 0 :
            # Remove Temp File
            tempFile = list(glob.glob(DataSetRootTrad+fileName+'*.inprogress'))[0]
            os.remove(tempFile)

def getSources(subItems):
    sources = []
    if 'Source' in subItems:
        if subItems['Source'] is not None:
            sources.append(parseSource(subItems['Source']))
    if 'Sources' in subItems:
        if subItems['Sources'] is not None:
            if ('#text' in subItems['Sources']['Source']) or isinstance(subItems['Sources']['Source'],str):
                subItems['Sources']['Source'] = [subItems['Sources']['Source']]
            for source in subItems['Sources']['Source']:
                sources.append(parseSource(source))
    return sources

def parseSource(elem):
    source = ''
    if isinstance(elem,str):
        source = ' Book: '+elem
    else:
        for key in reversed(elem.keys()):
            if key == "#text":
                source = source + ' Book: ' + elem[key]
            else:
                source = source + ' '+key+': ' + elem[key]
    return source

def getNameDesc(subItems):
    Name = sg.InputText(default_text=subItems['Name'],key='Name', metadata=['Name',subItems])
    layout = [[sg.Frame('Name: ',[[sg.Text(subItems['Name'],font=('Raleway', 12,'italic')),Name,sg.Button('Trad',key="Trad_Name",metadata=Name,pad=(10,10))]],font=('Raleway', 12,'bold'),pad=(6,10))], ]
    if 'Description' in subItems:
        if subItems['Description'] is not None:
            Description =  sg.Multiline(default_text=subItems['Description'],key='Description', metadata=['Description',subItems],size=(65,20),pad=(10,10))
            layout.append([sg.Frame('Description: ',[[sg.Multiline(default_text=subItems['Description'],text_color=sg.LOOK_AND_FEEL_TABLE[sg.theme()]['TEXT'],background_color=sg.LOOK_AND_FEEL_TABLE[sg.theme()]['BACKGROUND'],border_width=0,font=('Raleway', 12,'italic'),disabled=True,size=(65,22),pad=(10,10),key='Display_'),sg.Column([[Description],[sg.Button('Trad',key='Trad_Description',metadata=Description)]],element_justification='center')]],pad=(6,10),font=('Raleway', 12,'bold'))])
    return layout

def optionsParseXML(subItems,layout):
    optionsTab = []
    if 'OptionChoices' in subItems:
        if 'OptionChoice' in subItems['OptionChoices']:
            if 'Key' in subItems['OptionChoices']['OptionChoice']:
                subItems['OptionChoices']['OptionChoice'] = [subItems['OptionChoices']['OptionChoice']]
            for subItem in subItems['OptionChoices']['OptionChoice']:
                nameOpt = '_Option_'
                if 'Options' in subItem:
                    if 'Option' in subItem['Options']:
                        listOptions=[]
                        if 'Key' in subItem['Options']['Option']:
                            subItem['Options']['Option'] = [subItem['Options']['Option']]
                        for subsubItem in subItem['Options']['Option']:
                            bloc = []
                            for frame in getNameDesc(subsubItem):
                                bloc.append(frame)
                            listOptions.append([sg.Frame('',bloc)])
                if 'Name' in subItems:
                    nameOpt = subItems['Name']
                    listOptions.insert(0,[sg.Frame('Option Name: ',[[sg.Text(subItems['Name'],font=('Raleway', 12,'italic')),sg.InputText(default_text=subItems['Name'],key='Name', metadata=['Name',subItems])]],font=('Raleway', 12,'bold'),pad=(6,10))])
                optionsTab.append([sg.Tab(nameOpt,listOptions)])
    if 'Options' in subItems:
        if 'Option' in subItems['Options']:
            if 'Key' in subItems['Options']['Option']:
                subItems['Options']['Option'] = [subItems['Options']['Option']]
            for subItem in subItems['Options']['Option']:
                bloc = []
                for frame in getNameDesc(subItem):
                    bloc.append(frame)
                optionsTab.append([sg.Tab('_Option_',bloc   )])
    if len(optionsTab):
        layout.append([sg.Frame('Options',[[sg.TabGroup(optionsTab,key='Display_')]],font=('Raleway', 12,'bold'))])

def tradChoice(string):
    strTrad = []
    if settings['translators']['deepl']:
        strTrad.append(translateDeepl(string, sourceLang, targetLang, True))
    if settings['translators']['google'] or settings['translators']['bing']:
        for word in Glossary.keys():
            string = re.sub('(\W)'+word, '\\1'+Glossary[word].title(), string, flags=re.IGNORECASE)
        string = re.sub('(\[.{1,13}\])', '"\\1"', string, flags=re.IGNORECASE)
        if settings['translators']['google']:
            strTrad.append(re.sub('"(\[.{1,13}\])"', '\\1', ts.google(string, sourceLang, targetLang), flags=re.IGNORECASE))
        if settings['translators']['bing']:
            strTrad.append(re.sub('"(\[.{1,13}\])"', '\\1', ts.bing(string, sourceLang, targetLang), flags=re.IGNORECASE))
    return strTrad

def translateDeepl(string, sourceLang, targetLang, useGlossary):
    targetLang = targetLang.upper()
    driverPath = settings['Driver']
    if re.search('geckodriver',driverPath, re.IGNORECASE):
        browser = 'firefox'
        from selenium.webdriver.firefox.options import Options
        options = Options()
    elif re.search('chromedriver',driverPath, re.IGNORECASE):
        browser = 'chromium'
        from selenium.webdriver.chrome.options import Options
        options = Options()
    options.binary_location = settings['Browser']
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--headless')
    if browser == 'firefox':
        driver = webdriver.Firefox(options = options, executable_path = driverPath, service_log_path = 'nul')
    elif browser == 'chromium':
        driver = webdriver.Chrome(options = options, executable_path = driverPath)
    translatedArray = []
    driver.get('https://deepl.com/translator')
    languageSourceMenuButtonElement = driver.find_elements_by_css_selector('button[dl-test=translator-source-lang-btn]')
    languageSourceMenuButtonElement[0].click()
    driver.implicitly_wait(0.1)
    languageSourceButton = driver.find_elements_by_css_selector('button[dl-test$={0}'.format(sourceLang))
    driver.execute_script("arguments[0].click();", languageSourceButton[0])
    languageTargetMenuButtonElement = driver.find_elements_by_css_selector('button[dl-test=translator-target-lang-btn]')
    languageTargetMenuButtonElement[0].click()
    driver.implicitly_wait(0.1)
    languageTargetButton = driver.find_elements_by_css_selector('button[dl-test*={0}'.format(targetLang))
    driver.execute_script("arguments[0].click();", languageTargetButton[0])
    if useGlossary:
        trimGlossary = {}
        for word in Glossary.keys():
            if re.search('\W'+word, string, re.IGNORECASE):
                trimGlossary[word] = Glossary[word]

        glossaryElement = driver.find_elements_by_css_selector('#glossaryButton button')
        glossaryElement[0].click()
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#glossaryButton button')))
        finally:
            srcTextElement = driver.find_elements_by_css_selector('[dl-test="glossary-newentry-source-input"]')[0]
            targetTextElement = driver.find_elements_by_css_selector('[dl-test="glossary-newentry-target-input"]')[0]
            glossaryAcceptElement = driver.find_elements_by_css_selector('[dl-test="glossary-newentry-target-input"]')[0]
            glossaryCloseElement = driver.find_elements_by_css_selector('[dl-test="glossary-close-editor"]')[0]
            count = 0
            for word in trimGlossary.keys():
                count = count + 1
                if count > 10:
                    break
                srcTextElement.send_keys(word)
                targetTextElement.send_keys(Glossary[word])
                glossaryAcceptElement.click()
            glossaryCloseElement.click()
    textInputElement = driver.find_elements_by_css_selector('[dl-test="translator-source-input"]')[0]
    try:
        clearElement = driver.find_elements_by_css_selector('[dl-test="translator-source-clear-button"]')[0]
        clearElement.click()
    except:
        pass
    textInputElement.send_keys(string)
    while driver.find_element_by_xpath('//*[@id="dl_translator"]/div[1]/div[6]').get_attribute("class") == "lmt__mobile_share_container lmt__mobile_share_container--inactive":
        driver.implicitly_wait(0.1)
    driver.implicitly_wait(0.1)
    strTrad = driver.find_elements_by_css_selector('[dl-test="translator-target-result-as-text-entry"] button')[0].get_attribute("innerHTML")
    driver.quit()
    return(strTrad)

sg.theme('TanBlue')
main()