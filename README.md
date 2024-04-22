# Smart Attendance System

The Smart Attendance System automates attendance management, report generation, and notifications for staff and parents using facial recognition.

## Features

- Automated attendance capture
- Email reports to staff
- Send SMS notifications to parents
- Easy integration with JSON configuration

## Getting Started

1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/SmartAttendanceSystem.git
   ```

2. Install dependencies:
   ```sh
   pip install face_recognition numpy openpyxl twilio
   ```

3. Configure the system:
   - Create a `config.json` file with the required settings (see `config-example.json` for reference).
   - Set up Twilio account credentials in the code (`account_sid`, `auth_token`, `twilio_phone_number`).

4. Run the system:
   ```sh
   python attendance_system.py
   ```

## Usage

1. Capture attendance using facial recognition.
2. Mark students as present or absent based on recognized faces.
3. Generate attendance reports in an Excel file (`attendance.xlsx`).
4. Notify absent students' parents via SMS using Twilio.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please contact [My-email](govardhankumarv@gmail.com).

