Dim TimerActive As Boolean
Dim LastHash As String

Sub StartAutoSave()
    TimerActive = True
    LastHash = ComputeHash(ActiveDocument.Content.text)
    AutoSave
End Sub

Sub StopAutoSave()
    TimerActive = False
End Sub

Sub AutoSave()
    If TimerActive Then
        ' 获取当前文档的路径和名称
        Dim savePath As String
        Dim docName As String
        Dim timeStamp As String

        savePath = ActiveDocument.Path & "\"
        docName = "UndefinedName" '这里写你的文件原始名字
        timeStamp = Format(Now, "yyyy-mm-dd_HH-MM-SS")

        ' 计算当前文档内容的哈希值
        Dim currentHash As String
        currentHash = ComputeHash(ActiveDocument.Content.text)

        ' 检查文档内容是否有变化
        If currentHash <> LastHash Then
            ' 保存文档到当前文件夹，并附加时间戳，保存为 .docx 文件
            ActiveDocument.SaveAs2 FileName:=savePath & docName & "-" & "autobackup-" & timeStamp, FileFormat:=wdFormatXMLDocument

            ' 更新最后哈希值
            LastHash = currentHash

            ' 输出保存信息
            Debug.Print "Backup completed at " & Format(Now, "yyyy-mm-dd HH:MM:SS")
        Else
            ' 输出无变化信息
            Debug.Print "No changes detected at " & Format(Now, "yyyy-mm-dd HH:MM:SS")
        End If

        ' 每隔 5 分钟自动保存一次
        Application.OnTime Now + TimeValue("00:5:00"), "AutoSave"
    End If
End Sub

Function ComputeHash(text As String) As String
    Dim objSHA256 As Object
    Set objSHA256 = CreateObject("System.Security.Cryptography.SHA256Managed")
    Dim objEncoding As Object
    Set objEncoding = CreateObject("System.Text.UTF8Encoding")
    Dim bytes() As Byte
    bytes = objEncoding.GetBytes_4(text)
    Dim hash() As Byte
    hash = objSHA256.ComputeHash_2(bytes)
    Dim hashString As String
    Dim i As Integer
    For i = 0 To UBound(hash)
        hashString = hashString & Right("00" & Hex(hash(i)), 2)
    Next i
    ComputeHash = hashString
End Function
