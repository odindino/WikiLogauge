import pywikibot as pwb
from pywikibot import pagegenerators
from functools import partial


class wikiBot:
    def __init__(self):
        return

    def login(self):
        self.site.login()
        if self.check_login_state():
            self.InitalizeWiki()
        else:
            return

    def check_login_state(self):
        logged_in = self.site.logged_in()
        if logged_in:
            self.status.showMessage('login succed', msecs=5000)
            return True
        else:
            self.status.showMessage('login faild', msecs=5000)
            return False

    def show_wiki_page(self):
        login_state = self.check_login_state()
        page_name = self.lineEdit_wiki_page.text()
        if login_state:
            if page_name == '':
                page_name = '首頁'
            else:
                title_start = page_name.find('title=')
                if title_start != -1:
                    title_start += len("title=")
                    title_end = page_name.find("&", title_start)
                    if title_end == -1:
                        title_end = len(page_name)
                    title = page_name[title_start:title_end]
                    page_name = title
                else:
                    pass
            page_text = pwb.Page(self.site, page_name)
            page_text = page_text.text
            self.textBrowser_infinityWiki.setText(page_text)
        else:
            self.textBrowser_infinityWiki.setText('login failed')

    def wiki_recent_changed(self):
        login_state = self.check_login_state()
        if login_state:
            recent_changes = self.site.recentchanges(total=10)
            return recent_changes
        else:
            return

    # would like to add thread to upload file

    def wiki_upload(self):
        login_state = self.check_login_state()
        if login_state:
            for file in self.upload_list:
                [file_path, file_name, file_comment] = file
                file_page = pwb.FilePage(self.site, file_name)
                self.status.showMessage(file_name, msecs=5000)
                file_page.upload(file_path, ignore_warnings=True,
                                 comment='Uploaded via pywikibot')
            return
        else:
            return

    def wiki_text_sender(self, text):
        login_state = self.check_login_state()
        page_name = self.lineEdit_wiki_page.text()
        if login_state:
            page = pwb.Page(self.site, page_name)
            page.text += text
            page.save(text)
        else:
            self.check_login_statestatus.showMessage(
                'login failed', msecs=5000)
            return

    def InitalizeWiki(self):
        self.site = pwb.Site('zh-tw', 'infinitywiki')
        recent_changes = self.wiki_recent_changed()
        if recent_changes != None:
            i = 0
            for change in recent_changes:
                page = change['title']
                if i == 0:
                    self.lineEdit_wiki_page.setText(page)
                i += 1
                self.comboBox_wiki_recent_changes.addItem(page)
        else:
            page = 'login failed'

        text = 'Drop image file to upload to wiki\nPage = '
        page = self.lineEdit_wiki_page.text()
        self.label_drop_image_page.setText(text+page)

    def UserKeyInPage(self):
        page_title = self.lineEdit_wiki_page.text()
        self.label_drop_image_page.setText(page_title)
        self.show_wiki_page()

    def wiki_recent_page_select(self):
        page = self.comboBox_wiki_recent_changes.currentText()
        self.lineEdit_wiki_page.setText(page)
        self.show_wiki_page()
        text = 'Drop image file to upload to wiki, Page = '
        self.label_drop_image_page.setText(text+page)

    def upload_to_wiki(self):
        self.wiki_upload()
        image_format_before = '''<li style="display: inline-block; vertical-align: top;">[[檔案:'''
        image_format_middle = '|無|縮圖|'
        image_format_after = "]]</li>"
        if len(self.upload_list) != 1:
            self.wiki_text_sender("\n<div><ul>")
        for upload_file in self.upload_list:
            [drop_path, file_name, file_comment] = upload_file
            text = image_format_before+file_name+image_format_middle + \
                file_name+'<br>'+file_comment+image_format_after+'\n'
            self.wiki_text_sender(text)
        if len(self.upload_list) != 1:
            self.wiki_text_sender("\n</ul></div>")
        self.status.showMessage('wiki_text_sender', msecs=5000)
        self.listWidget_drop_file.clear()
        self.textEdit_drop_file_name.setText('')
        self.textEdit_drop_file_comment.setText('')
        self.textBrowser_image_text_format.setText('')
        self.textEdit_send_text.setPlainText('')
        self.show_wiki_page()
        self.upload_list = []

    def upload_name_changed(self):
        if self.upload_list == []:
            self.pushButton_upload_file_to_wiki.setEnabled(False)
            return
        else:
            index = self.listWidget_drop_file.currentRow()
            self.upload_list[index][1] = self.textEdit_drop_file_name.toPlainText()
            self.upload_list[index][2] = self.textEdit_drop_file_comment.toPlainText(
            )
        text = ''
        for upload_file in self.upload_list:
            [drop_path, file_name, file_comment] = upload_file
            image_format_before = '''<li style="display: inline-block; vertical-align: top;">[[檔案:'''
            image_format_middle = '|無|縮圖|'
            image_format_after = "]]</li>"
            if file_comment != '':
                file_comment = '<br>'+file_comment
            text = text+image_format_before+file_name+image_format_middle + \
                file_name+file_comment+image_format_after+'\n'
        self.textBrowser_image_text_format.setText(text)
        self.pushButton_upload_file_to_wiki.setEnabled(True)

    def send_text_to_wiki(self):
        page_name = self.lineEdit_wiki_page.text()
        send_text = self.textEdit_send_text.toPlainText()+'\n'
        if send_text.startswith("=="):
            send_text = '\n'+send_text
        else:
            send_text = '\n<br>'+send_text
        self.status.showMessage('wiki_text_sender', msecs=5000)
        self.wiki_text_sender(send_text)
        self.textEdit_send_text.setText('')
        self.show_wiki_page()

    def drop_file_order_changed(self, move_order):
        index = self.listWidget_drop_file.currentRow()
        if move_order == 'up' and index != 0:
            self.upload_list.insert(index-1, self.upload_list.pop(index))
            file_name = self.upload_list[index][0]
            item = self.listWidget_drop_file.item(index)
            item.setText(file_name)
            file_name = self.upload_list[index-1][0]
            item = self.listWidget_drop_file.item(index-1)
            item.setText(file_name)
            self.listWidget_drop_file.setCurrentRow(index-1)
        elif move_order == 'down' and index != len(self.upload_list)-1:
            self.upload_list.insert(index + 1, self.upload_list.pop(index))
            file_name = self.upload_list[index][0]
            item = self.listWidget_drop_file.item(index)
            item.setText(file_name)
            file_name = self.upload_list[index+1][0]
            item = self.listWidget_drop_file.item(index+1)
            item.setText(file_name)
            self.listWidget_drop_file.setCurrentRow(index+1)
        else:
            return
        self.upload_name_changed()

    def handle_wiki_item_clicked(self, item):
        index = self.listWidget_drop_file.row(item)
        try:
            file_name = self.upload_list[index][1]
            file_comment = self.upload_list[index][2]
            self.textEdit_drop_file_name.setText(file_name)
            self.textEdit_drop_file_comment.setText(file_comment)
        except IndexError:
            print('index error')

    def clear_upload_list(self):
        self.upload_list = []
        self.listWidget_drop_file.clear()
        self.textEdit_drop_file_name.setText('')
        self.textEdit_drop_file_comment.setText('')
        self.textBrowser_image_text_format.setText('')
        self.textEdit_send_text.setPlainText('')
