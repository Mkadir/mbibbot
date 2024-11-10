from datetime import datetime

from sqlalchemy.orm import Session
from .models import Tests, TestQuestions, Users, Results
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from sqlalchemy import select
from typing import Dict, List


# Fetch all tests
def get_tests(db: Session):
    return db.query(Tests).all()


# Fetch a specific test by its ID
def get_test_by_id(db: Session, test_id: int):
    return db.query(Tests).filter(Tests.id == test_id).first()


# Fetch all test questions
def get_test_questions(db: Session):
    return db.query(TestQuestions).all()


# Fetch a specific question by its ID
def get_question_by_id(db: Session, question_id: int):
    return db.query(TestQuestions).filter(TestQuestions.id == question_id).first()


# Fetch questions by test ID
def get_questions_by_id(db: Session, test_id: int):
    return db.query(TestQuestions).filter(TestQuestions.test_id == test_id).all()


# Add a new test
def add_test(db: Session, title: str):
    new_test = Tests(title=title)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test


# Add a question to a test
def add_test_question(db: Session, question: str, test_id: int, options: str, correct_option: int,
                      media_content: str = None, media_type: str = None):
    new_question = TestQuestions(
        question=question,
        test_id=test_id,
        options=options,
        correct_option=correct_option,
        media_content=media_content,
        media_type=media_type
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


# Delete a test by its ID
def delete_test(db: Session, test_id: int):
    test_to_delete = db.query(Tests).filter(Tests.id == test_id).first()
    if test_to_delete:
        db.delete(test_to_delete)
        db.commit()
        return True
    return False


# Delete a question by its ID
def delete_test_question(db: Session, question_id: int):
    question_to_delete = db.query(TestQuestions).filter(TestQuestions.id == question_id).first()
    if question_to_delete:
        db.delete(question_to_delete)
        db.commit()
        return True
    return False


# Update the poll ID of a question
def update_question(db: Session, question_id: int, poll_id: str):
    question = db.query(TestQuestions).filter(TestQuestions.id == question_id).first()
    if question:
        question.poll_id = poll_id
        db.commit()
        db.refresh(question)
        return question
    return None


# Fetch a user by Telegram ID
def get_user_by_tg_id(db: Session, tg_id: int):
    return db.query(Users).filter(Users.tg_id == tg_id).first()


# Fetch a question by poll ID
def get_question_by_pool_id(db: Session, poll_id: str):
    return db.query(TestQuestions).filter(TestQuestions.poll_id == poll_id).first()


# Add a result for a question
def add_result_question(db: Session, poll_id: str, user_id: int, selected_option: int):
    question = get_question_by_pool_id(db=db, poll_id=poll_id)
    user = get_user_by_tg_id(db=db, tg_id=user_id)
    if question and user:
        result = Results(
            test_id=question.test_id,
            question_id=question.id,
            user_id=user.id,
            selected_option=selected_option,
            is_correct=(selected_option == int(question.correct_option))
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    return None


# Add a new user
def add_user(db: Session, tg_id: int, full_name: str, username: str = None, phone_number: str = None):
    user = Users(
        tg_id=tg_id,
        username=username,
        full_name=full_name,
        phone_number=phone_number
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except:
        db.rollback()
        return None
    return user


# Update an existing user by user ID
def update_user(db: Session, user_id: int, data: Dict[str, Any]) -> Optional[Users]:
    """
    Update user data in the database.

    Args:
        db: SQLAlchemy database session
        user_id: ID of the user to update
        data: Dictionary containing fields to update

    Returns:
        Updated user object or None if user not found
    """
    try:
        # Start transaction
        user = db.query(Users).filter(Users.tg_id == user_id).first()

        if not user:
            return None

        # Filter out invalid fields and None values
        valid_fields = {
            key: value
            for key, value in data.items()
            if hasattr(user, key) and value is not None
        }

        if not valid_fields:
            return user

        # Update user fields
        for key, value in valid_fields.items():
            setattr(user, key, value)

        # Commit changes
        db.commit()
        db.refresh(user)

        return user

    except SQLAlchemyError as e:
        # Rollback in case of error
        db.rollback()
        raise Exception(f"Failed to update user: {str(e)}")

    except Exception as e:
        db.rollback()
        raise Exception(f"Unexpected error: {str(e)}")


# Helper function to get existing answer (should be in your database logic)
def get_existing_answer(db: Session, poll_id: str, user_id: int):
    # Query Results, joining with TestQuestions to filter by poll_id
    return db.query(Results).join(TestQuestions).filter(
        TestQuestions.poll_id == poll_id,
        Results.user_id == user_id
    ).first()


def get_test_results(db: Session, test_id: int):
    test_result = db.query(Results).filter(
        Results.test_id == test_id
    ).all()

    return test_result

import os
def clean_text(text):
    """Ensures the text is UTF-8 encoded, replacing errors if found."""
    if isinstance(text, str):
        return text.encode("utf-8", errors="replace").decode("utf-8")
    return text


def export_users_to_excel(db: Session):
    """
    Export all users to a professionally formatted Excel file with proper styling,
    column widths, and headers.

    :param db: Database session
    :return: Path to the Excel file
    """
    # Query all users
    users = db.query(Users).all()

    # Extract and clean data into a list of dictionaries
    data = [
        {
            "ID": user.id,
            "Telegram ID": user.tg_id,
            "Username": clean_text(user.username),
            "Full Name": clean_text(user.full_name),
            "Phone Number": clean_text(user.phone_number),
            "Region": clean_text(user.region),
            "Verified": user.verified
        }
        for user in users
    ]

    # Convert data to a DataFrame
    df = pd.DataFrame(data)

    # Create Excel writer with xlsxwriter engine for better formatting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join("exports", f"users_export_{timestamp}.xlsx")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Users', index=False)

    # Get workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Users']

    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 11,
        'font_name': 'Calibri'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'font_size': 10,
        'font_name': 'Calibri',
        'text_wrap': True
    })

    number_format = workbook.add_format({
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'font_size': 10,
        'font_name': 'Calibri'
    })

    verified_format_true = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 10,
        'font_name': 'Calibri',
        'bg_color': '#E2EFDA',  # Light green
        'font_color': '#375623'  # Dark green
    })

    verified_format_false = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 10,
        'font_name': 'Calibri',
        'bg_color': '#FFF2F2',  # Light red
        'font_color': '#843C39'  # Dark red
    })

    # Apply header format
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Write data with formatting
    for row_num in range(len(df)):
        for col_num, value in enumerate(df.iloc[row_num]):
            # Special formatting for verified status
            if df.columns[col_num] == 'Verified':
                if value:
                    worksheet.write(row_num + 1, col_num, 'Yes', verified_format_true)
                else:
                    worksheet.write(row_num + 1, col_num, 'No', verified_format_false)
            # Number formatting for IDs
            elif df.columns[col_num] in ['ID', 'Telegram ID']:
                worksheet.write(row_num + 1, col_num, value, number_format)
            # Default cell formatting
            else:
                worksheet.write(row_num + 1, col_num, value, cell_format)

    # Set column widths based on content
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = max(
            series.astype(str).apply(len).max(),  # max length of values
            len(str(col))  # length of column name
        ) + 3  # padding
        worksheet.set_column(idx, idx, min(max_len, 30))  # Cap width at 30

    # Freeze the header row
    worksheet.freeze_panes(1, 0)

    # Add alternating row colors for better readability
    worksheet.set_row(0, 20)  # Set header height
    for row in range(1, len(df) + 1):
        if row % 2 == 0:
            worksheet.set_row(row, 15, workbook.add_format({'bg_color': '#F8F9FA'}))
        else:
            worksheet.set_row(row, 15)

    # Add a total count at the bottom
    summary_row = len(df) + 2
    bold_format = workbook.add_format({'bold': True})
    worksheet.write(summary_row, 0, f"Total Users: {len(df)}", bold_format)

    # Save and close
    writer.close()

    return file_path


def export_results_to_excel(db: Session, test_id: int) -> str:
    """
    Test natijalarini yaxshilangan uslub bilan, sarlavha formatlash va
    ko'rsatkichlarga asoslangan rang kodlash bilan professional shakldagi Excel faylga eksport qilish.

    Ko'rsatkichlar darajalari:
    - A'lo (To'q yashil): ≥80% to'g'ri
    - Qoniqarli (To'q sariq): 50-79% to'g'ri
    - Yaxshilash zarur (To'q qizil): <50% to'g'ri

    Argumentlar:
        db: SQLAlchemy ma'lumotlar bazasi sessiyasi
        test_id: eksport qilinadigan test IDsi

    Qaytadi:
        str: yaratilgan Excel fayl yo'li
    """
    # Ma'lumotlar bazasi so'rovlari (o'zgarmagan)
    test = db.query(Tests).filter(Tests.id == test_id).first()
    if not test:
        raise ValueError(f"Test ID {test_id} topilmadi")

    questions = db.query(TestQuestions).filter(
        TestQuestions.test_id == test_id
    ).order_by(TestQuestions.id).all()

    results = db.query(Results).filter(
        Results.test_id == test_id
    ).all()

    participant_ids = {result.user_id for result in results}
    participants = db.query(Users).filter(Users.id.in_(participant_ids)).all()
    non_participants = db.query(Users).filter(
        ~Users.id.in_(participant_ids)
    ).all()

    # Ma'lumotlarni tayyorlash (aslga o'xshash)
    user_answers = {}
    user_scores = {}
    for result in results:
        if result.user_id not in user_answers:
            user_answers[result.user_id] = {}
            user_scores[result.user_id] = 0
        user_answers[result.user_id][result.question_id] = "To'g'ri" if result.is_correct else "Xato"
        if result.is_correct:
            user_scores[result.user_id] += 1

    # Tuzilgan DataFrame ma'lumotlarini tayyorlash
    data = []
    total_questions = len(questions)

    # Qatnashgan foydalanuvchilar ma'lumotlari qo'shiladi
    for user in participants:
        correct_answers = user_scores.get(user.id, 0)
        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        row = {
            "F.I.SH": user.full_name or "N/A",
            "Hudud": user.region or "N/A",
            "Test nomi": test.title,
            "To'g'ri javoblar": correct_answers,
            "Umumiy savollar": total_questions,
            "Foiz": f"{percentage:.1f}%",
            "Baho": _baho_olish(percentage),
            "Status": "Qatnashgan"
        }

        # Har bir savol uchun javoblarni qo'shish
        for i, question in enumerate(questions, 1):
            row[f"{i}-Savol"] = user_answers.get(user.id, {}).get(question.id, "Javob bermagan")

        row["SortScore"] = percentage
        data.append(row)

    # Qatnashmagan foydalanuvchilar ma'lumotlari qo'shiladi
    for user in non_participants:
        row = {
            "F.I.SH": user.full_name or "N/A",
            "Hudud": user.region or "N/A",
            "Test nomi": test.title,
            "To'g'ri javoblar": 0,
            "Umumiy savollar": total_questions,
            "Foiz": "0.0%",
            "Baho": "F",
            "Status": "Qatnashmagan"
        }

        for i in range(1, total_questions + 1):
            row[f"{i}-Savol"] = "Javob bermagan"

        row["SortScore"] = -1
        data.append(row)

    # DataFrame yaratish va saralash
    df = pd.DataFrame(data)
    df = df.sort_values(by=['SortScore', 'F.I.SH'], ascending=[False, True])

    # Vaqt belgisi bilan chiqish fayl nomini yaratish
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_{test_id}_natijalar_{timestamp}.xlsx"

    # Excel yozuvchini yaratish
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

    # Saralash ustunini tushirib, eksport qilish
    df_export = df.drop(['SortScore'], axis=1)
    df_export.to_excel(writer, index=False, sheet_name='Natijalar')

    # Ishchi daftar va varaqlarni olish
    workbook = writer.book
    worksheet = writer.sheets['Natijalar']

    # Formatlar aniqlash - TO'QROQ RANGLAR
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',  # Standard Excel blue
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 12,
        'font_name': 'Arial'
    })

    excellent_format = workbook.add_format({
        'bg_color': '#9DC3E6',  # Light professional blue
        'font_color': '#1F497D',  # Dark blue text
        'border': 1,
        'align': 'center'
    })

    satisfactory_format = workbook.add_format({
        'bg_color': '#FFE699',  # Soft yellow
        'font_color': '#7F6000',  # Dark brown text
        'border': 1,
        'align': 'center'
    })

    needs_improvement_format = workbook.add_format({
        'bg_color': '#FF9999',  # Soft red
        'font_color': '#843C39',  # Dark red text
        'border': 1,
        'align': 'center'
    })

    not_participated_format = workbook.add_format({
        'bg_color': '#F2F2F2',  # Light gray
        'font_color': '#595959',  # Dark gray text
        'border': 1,
        'align': 'center'
    })

    # Sarlavhalarni formatlash
    for col_num, value in enumerate(df_export.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Shartli formatlash va chegaralarni qo'llash
    first_row = 1
    last_row = len(df)
    last_col = len(df_export.columns) - 1

    for row_num in range(first_row, last_row + 1):
        percentage = float(df.iloc[row_num - 1]['Foiz'].rstrip('%'))
        status = df.iloc[row_num - 1]['Status']

        if status == "Qatnashmagan":
            format_to_apply = not_participated_format
        elif percentage >= 80:
            format_to_apply = excellent_format
        elif percentage >= 50:
            format_to_apply = satisfactory_format
        else:
            format_to_apply = needs_improvement_format

        worksheet.set_row(row_num, None, format_to_apply)

    # Hamma kataklarga chegaralar qo'shish
    worksheet.conditional_format(0, 0, last_row, last_col, {
        'type': 'no_blanks',
        'format': workbook.add_format({'border': 1})
    })

    # Sovuq plitalar qo'yish
    worksheet.freeze_panes(1, 0)

    # Ustun kengliklarini o'rnatish
    for i, column in enumerate(df_export.columns):
        max_length = max(
            df_export[column].astype(str).apply(len).max(),
            len(column)
        ) + 2
        worksheet.set_column(i, i, min(max_length, 30))

    # Yig'indini qo'shish
    summary_row = last_row + 3
    bold_format = workbook.add_format({'bold': True})

    worksheet.write(summary_row, 0, "Test Yig'indisi:", bold_format)
    worksheet.write(summary_row + 1, 0, f"Umumiy Qatnashchilar: {len(participants)}")
    worksheet.write(summary_row + 2, 0, f"Qatnashmaganlar: {len(non_participants)}")
    worksheet.write(summary_row + 3, 0, f"O'rtacha Natija: {df['Foiz'].str.rstrip('%').astype(float).mean():.1f}%")

    # Izoh
    legend_row = summary_row
    worksheet.write(legend_row, 3, "Ko'rsatkich Izohi:", bold_format)
    worksheet.write(legend_row + 1, 3, "≥80%", excellent_format)
    worksheet.write(legend_row + 2, 3, "50-79%", satisfactory_format)
    worksheet.write(legend_row + 3, 3, "<50%", needs_improvement_format)
    worksheet.write(legend_row + 4, 3, "Qatnashmagan", not_participated_format)

    # Saqlash va yopish
    writer.close()
    return output_file


def _baho_olish(correct_answers: int) -> int:
    """Har bir to'g'ri javob uchun bitta ball qaytaruvchi yordamchi funksiya."""
    return correct_answers