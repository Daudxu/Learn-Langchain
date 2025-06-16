import nodemailer from 'nodemailer';

async function sendEmail() {
  try {
    // 注意：是 createTransport，不是 createTransporter
    const transporter = nodemailer.createTransport({
      host: 'smtp.mailgun.org',
      port: 587,
      secure: false,
      auth: {
        user: 'asdasd@assad.io',
        pass: 'asdasdasd'
      }
    });

    const mailOptions = {
      from: 'asdasd@assad.io',
      to: 'asdasd@gmail.com',
    //   to: 'xudan@apowo.com',
      subject: 'Hello',
      text: 'Testing some Mailgun awesomness!'
    };

    const info = await transporter.sendMail(mailOptions);
    console.log('邮件发送成功:', info.response);
  } catch (error) {
    console.error('发送失败:', error);
  }
}

sendEmail();