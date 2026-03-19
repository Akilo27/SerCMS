from googletrans import Translator
import os


def translate_po_file(filepath, dest_lang="uz"):  # 'tg' — таджикский
    translator = Translator()
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    current_msgid = None
    inside_msgstr = False

    translated_count = 0
    skipped_count = 0
    error_count = 0

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("msgid"):
            current_msgid = stripped[6:].strip().strip('"')
            output_lines.append(line)
            inside_msgstr = False

        elif stripped.startswith("msgstr"):
            if current_msgid:
                if '""' in line:
                    try:
                        translated = translator.translate(
                            current_msgid, dest=dest_lang
                        ).text
                        print(
                            f'[Переведено] "{current_msgid}" → "{translated}"'
                        )  # Печать онлайн
                        output_lines.append(f'msgstr "{translated}"\n')
                        translated_count += 1
                    except Exception as e:
                        print(f'[Ошибка] "{current_msgid}": {e}')
                        error_count += 1
                        output_lines.append(line)
                else:
                    skipped_count += 1
                    output_lines.append(line)
            else:
                output_lines.append(line)
            current_msgid = None
            inside_msgstr = True

        elif inside_msgstr and stripped.startswith('"'):
            continue
        else:
            output_lines.append(line)

    backup = filepath + ".backup"
    os.rename(filepath, backup)
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(
        f"\nПеревод завершён: переведено {translated_count} строк, пропущено {skipped_count}, ошибок {error_count}."
    )


translate_po_file("django.po", "uz")
