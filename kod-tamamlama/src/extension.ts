import * as vscode from 'vscode';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    console.log('Kod Tamamlama Eklentisi aktif!');
    
    // Ctrl+Space tuş kombinasyonu için komut ekleyin
    let disposable = vscode.commands.registerCommand('extension.getPrediction', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const document = editor.document;
            const selection = editor.selection;
            
            // İmlecin bulunduğu konumu alın
            const position = selection.active;
            
            // İmlecin bulunduğu satırdan önceki son 3 satırı alın
            const line = position.line;
            const startLine = Math.max(0, line - 3); // En az 0. satırdan başla
            const endLine = line;
            
            const range = new vscode.Range(
                new vscode.Position(startLine, 0),
                new vscode.Position(endLine, document.lineAt(endLine).text.length)
            );
            
            const text = document.getText(range);
            
            if (!text) {
                vscode.window.showErrorMessage('Kod bulunamadı!');
                return;
            }
            
            try {
                // Flask API'nize istek gönderin
                const response = await axios.post('http://localhost:5000/tahmin', {
                    kod: text
                });
                
                const prediction = response.data.tahmin;
                
                // Tahmini otomatik olarak editöre ekleyin
                if (prediction) {
                    editor.edit(editBuilder => {
                        // Tahmini imlecin bulunduğu konuma ekle
                        editBuilder.insert(position, prediction);
                    });
                    
                    // İsteğe bağlı olarak kullanıcıya bildirim gösterin
                    vscode.window.setStatusBarMessage(`Kod önerisi eklendi!`, 3000);
                } else {
                    vscode.window.showErrorMessage('Tahmin alınamadı!');
                }
            } catch (error: any) {
                vscode.window.showErrorMessage('API isteği başarısız oldu: ' + error.message);
            }
        }
    });
    
    // Komutu eklentiye ekleyin
    context.subscriptions.push(disposable);
    
    // Ctrl+Space tuş kombinasyonunu tanımlayın
    context.subscriptions.push(
        vscode.commands.registerCommand('extension.ctrlSpace', () => {
            vscode.commands.executeCommand('extension.getPrediction');
        })
    );
}

export function deactivate() {}