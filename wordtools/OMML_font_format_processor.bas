Attribute VB_Name = "OMML公式批量字体转换"
' (o′ω`o)? Master~ Your new custom-made code is here~
' 这个宏会批量转换 Word 文档中的公式字体，
' 只对半角字符出手，并且会保留斜体状态。
Sub BatchChangeEquationFont_NoItalicNumbers()
    ' 准备工具...
    Dim oMath As Word.oMath
    Dim doc As Word.Document
    Dim equationRange As Word.Range
    Dim targetRange As Word.Range
    Dim singleChar As Word.Range
    Dim charCode As Integer
    Dim isItalic As Boolean
    Dim hashPos As Integer
    Dim counter As Long
    
    Set doc = ActiveDocument
    counter = 0

    Application.ScreenUpdating = False

    ' 开始！
    For Each oMath In doc.OMaths
        Set equationRange = oMath.Range
        
        ' 寻找“#”
        hashPos = InStr(1, equationRange.text, "#")

        If hashPos > 0 Then
            ' 只修改“#”前面的部分
            Set targetRange = doc.Range(equationRange.Start, equationRange.Start + hashPos - 1)
        Else
            ' 没有“#”？那整个都是我们的！
            Set targetRange = equationRange
        End If

        ' 开始一个一个地转换...
        For Each singleChar In targetRange.Characters
            ' 只对半角字符出手
            If AscW(singleChar.text) >= 0 And AscW(singleChar.text) <= 255 Then

                ' 先判断它是不是一个数字...
                If IsNumeric(singleChar.text) Then
                    singleChar.Font.Name = "Times New Roman"
                    singleChar.Font.Italic = False
                Else
                    ' 记住斜体状态...
                    isItalic = singleChar.Font.Italic
                    ' 更换字体...
                    singleChar.Font.Name = "Times New Roman"
                    ' 保持斜体状态...
                    singleChar.Font.Italic = isItalic
                End If

            End If
        Next singleChar
        
        counter = counter + 1
    Next oMath

    Application.ScreenUpdating = True

    MsgBox "处理完毕。" & vbCrLf & "共 " & counter & " 个公式已按新规则更新。", vbInformation, "小猫的处理报告"

End Sub
