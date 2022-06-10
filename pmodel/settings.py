from plibs import *
from pheader import *
from pcontroller import pupdater, payromasdk, event, translator, ThreadingResult, ThreadingArea
from pui import settings, fonts, images, styles, Size


class SettingsModel(settings.UiForm, event.EventForm):
    def __init__(self, parent):
        super(SettingsModel, self).__init__(parent)

        self.setup()
        self.events_listening()

        # Threading Methods
        self.__backupThread = ThreadingArea(self.__backup_clicked_core)
        self.__backupThread.signal.resultSignal.connect(self.__backup_clicked_ui)
        self.__backupThread.finished.connect(self.backup_completed)

        self.__importThread = ThreadingArea(self.__import_clicked_core)
        self.__importThread.signal.resultSignal.connect(self.__import_clicked_ui)
        self.__importThread.signal.normalSignal.connect(self.__import_password_required)
        self.__importThread.finished.connect(self.import_completed)

        self.__autoUpdateThread = ThreadingArea(self.__auto_update_core)
        self.__autoUpdateThread.signal.resultSignal.connect(self.__auto_update_ui)
        self.__autoUpdateThread.signal.normalSignal.connect(self.__auto_update_ask)

        # Variables
        self.__backupPassword = None
        self.__backupFilePath = None
        self.__updateAccepted = None

    def app_started_event(self):
        self.__autoUpdateThread.start()

    def network_changed_event(self, name: str, status: bool):
        self.set_data(status, name)

    @pyqtSlot(bool)
    def switch_clicked(self, state: bool):
        theme_name = 'dark' if state else ''
        event.themeChanged.notify(name=theme_name)
        Global.settings.update_option(SettingsOption.themeName, theme_name)

    @pyqtSlot()
    def network_clicked(self):
        event.mainTabChanged.notify(tab=Tab.NETWORKS_LIST)

    @pyqtSlot()
    def backup_clicked(self):
        if self.__backupThread.isRunning():
            return
        elif payromasdk.data.wallets.db.count == 0:
            QApplication.quickNotification.warning(translator("No data to backup yet"))
            return

        # Save directory
        default_path = os.path.join(
            Dir.DESKTOP, '%s %s.%s' % (
                payromasdk.data.wallets.db.config.backupFileName.title(),
                time.ctime().replace(':', '-'),
                payromasdk.data.wallets.db.config.backupExtension
            )
        )
        self.__backupFilePath = QFileDialog().getSaveFileName(
            self, 'Save File', default_path, options=QFileDialog.ShowDirsOnly
        )[0]
        if not self.__backupFilePath:
            return

        # Default password
        self.__backupPassword = payromasdk.data.wallets.db.password

        # Ask to set a password
        title = translator("Do you want to set a special password for the backup file?")
        description = translator("Note: The file will be encrypted anyway.")
        html_message = '<h3>%s</h3><ul>* %s</ul>' % (title, description)
        messagebox = SPGraphics.MessageBoxConfirm(
            parent=self,
            text=html_message,
            icon=images.data.icons.info41,
            color=styles.data.colors.font.name(),
            accept=translator("Yes, Set a Password"),
            cancel=translator("No, Backup Now"),
            window_size=Size.messageBox
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.labelMessage.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        messagebox.exec_()

        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            # Set new password
            title = translator("Set your protection password")
            description = translator("Note: You can't import without this password.")
            html_message = '<h3>%s</h3><ul>* %s</ul>' % (title, description)
            title2 = translator("Confirm your password again")
            html_message2 = '<h2>%s</h2>' % title2
            title3 = translator(
                "Password must be good at least and including UPPER/lowercase, symbols and numbers."
            )
            html_message3 = '<h3>%s</h3>' % title3
            messagebox = SPGraphics.MessageBoxPasswordMatching(
                parent=self,
                text=html_message,
                text_again=html_message2,
                text_weak_password=html_message3,
                icon=images.data.icons.info41,
                color=styles.data.colors.font.name(),
                window_size=Size.messageBox
            )
            messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
            messagebox.labelMessage.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            messagebox.exec_()

            if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
                if messagebox.isVerified:
                    self.__backupPassword = messagebox.password
                else:
                    QApplication.quickNotification.warning(translator("Password doesn't match."))
                    return

        if messagebox.clickedOn is SPGraphics.Button.CLOSE:
            return

        # Start backup
        super(SettingsModel, self).backup_clicked()
        self.__backupThread.start()

    def __backup_clicked_core(self):
        result = ThreadingResult(
            message=translator("Failed to backup, Please try again.")
        )

        try:
            result.isValid = payromasdk.engine.wallet.backup_wallets(
                path=self.__backupFilePath, password=self.__backupPassword
            )
            if result.isValid:
                result.message = translator("Backup completed successfully.")

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__backupThread.signal.resultSignal.emit(result)

    @staticmethod
    def __backup_clicked_ui(result: ThreadingResult):
        result.show_message()

    @pyqtSlot()
    def import_clicked(self):
        if self.__importThread.isRunning():
            return

        files_filter = '*%s.%s' % (payromasdk.data.wallets.db.config.backupExtension, SPCrypto.AESInfo.EXTENSION)
        browser = QFileDialog(self, 'File Browser', Dir.DESKTOP, files_filter)
        browser.setFileMode(QFileDialog.ExistingFiles)
        if browser.exec_() != QDialog.Accepted:
            return

        self.__backupFilePath = browser.selectedFiles()[0]

        # Default password
        self.__backupPassword = payromasdk.data.wallets.db.password

        super(SettingsModel, self).import_clicked()
        self.__importThread.start()

    def __import_clicked_core(self):
        result = ThreadingResult(
            message=translator("Decryption password is wrong!")
        )

        try:
            for attempt in range(2):
                try:
                    result.isValid = payromasdk.engine.wallet.import_wallets(
                        path=self.__backupFilePath, password=self.__backupPassword, mode=SPDatabase.Control.SET
                    )
                    if result.isValid:
                        result.message = translator("Import completed successfully.")
                        break

                except PermissionError:
                    if attempt == 0:
                        self.__importThread.signal.normalSignal.emit()
                        while self.__backupPassword == payromasdk.data.wallets.db.password:
                            time.sleep(1)

        except Exception as err:
            result.error(str(err))

        time.sleep(3)
        self.__importThread.signal.resultSignal.emit(result)

    @staticmethod
    def __import_clicked_ui(result: ThreadingResult):
        if result.isValid:
            event.walletEdited.notify()
            event.mainTabChanged.notify(tab=Tab.WALLETS_LIST)

        result.show_message()

    def __import_password_required(self):
        messagebox = SPGraphics.MessageBoxPassword(
            parent=self,
            text=translator("Password confirmation is required."),
            font_size=fonts.data.size.title,
            color=styles.data.colors.font.name(),
            window_size=Size.messageBox
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.labelMessage.setAlignment(Qt.AlignCenter)
        messagebox.exec_()
        self.__backupPassword = messagebox.password

    def __auto_update_core(self):
        result = ThreadingResult(
            message=translator("Failed to update the application."),
            params={
                'inProgress': False
            }
        )

        try:
            is_updated = pupdater.is_updated(default=True)

            if not is_updated:
                self.__autoUpdateThread.signal.normalSignal.emit()
                while self.__updateAccepted is None:
                    time.sleep(1)

            if self.__updateAccepted:
                result.params['inProgress'] = True

                if pupdater.download():
                    result.isValid = True

                if result.isValid:
                    result.message = translator("Application updated successfully.")

        except Exception as err:
            result.error(str(err))

        self.__autoUpdateThread.signal.resultSignal.emit(result)

    def __auto_update_ui(self, result: ThreadingResult):
        self.__updateAccepted = None
        if result.params['inProgress']:
            result.show_message()

        if result.isValid:
            messagebox = SPGraphics.MessageBoxConfirm(
                parent=self,
                text=translator("Application needs to restart to update."),
                font_size=fonts.data.size.title,
                color=styles.data.colors.font.name(),
                accept=translator("Restart"),
                cancel=translator("Later")
            )
            messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
            messagebox.labelMessage.setAlignment(Qt.AlignCenter)
            messagebox.exec_()

            if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
                psutil.Popen(f'"{SOFTWARE_NAME} Update.exe" {os.getpid()} {Website.UPDATER_API}')

    def __auto_update_ask(self):
        messagebox = SPGraphics.MessageBoxConfirm(
            parent=self,
            text=translator("A new version of {} is available!").format(SOFTWARE_NAME),
            font_size=fonts.data.size.title,
            color=styles.data.colors.font.name(),
            accept=translator("Update"),
            cancel=translator("Later")
        )
        messagebox.frame.layout().setContentsMargins(21, 11, 21, 11)
        messagebox.labelMessage.setAlignment(Qt.AlignCenter)
        messagebox.exec_()

        if messagebox.clickedOn is SPGraphics.Button.ACCEPT:
            QApplication.quickNotification.information(
                translator("Please wait, updates are downloading..."), timeout=3000
            )
            self.__updateAccepted = True
        else:
            self.__updateAccepted = False
