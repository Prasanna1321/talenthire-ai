import emailjs from "@emailjs/browser";

const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID;
const TEMPLATE_ID = import.meta.env.VITE_EMAILJS_TEMPLATE_ID;
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY;

emailjs.init({
  publicKey: PUBLIC_KEY,
});

export const sendOtpEmail = async (email, name, otp) => {
  try {
    const templateParams = {
      email: email,
      name: name,
      otp: otp,
    };

    const response = await emailjs.send(
      SERVICE_ID,
      TEMPLATE_ID,
      templateParams
    );

    console.log("✅ Email sent successfully:", response);

    return true;
  } catch (error) {
    console.error("❌ EmailJS error:", error);

    return false;
  }
};