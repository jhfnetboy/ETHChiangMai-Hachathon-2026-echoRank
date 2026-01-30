import sgMail from "@sendgrid/mail";

export function initSendGrid(key: string) {
  sgMail.setApiKey(key);
}

export async function sendRegisterEmail(to: string, from: string, code: string, baseUrl: string) {
  const msg = {
    to,
    from,
    subject: "echoRank 注册验证",
    text: `您的验证码：${code}\n如果是点击验证链接，请访问：${baseUrl}`,
    html: `<p>您的验证码：<strong>${code}</strong></p><p>如果是点击验证链接，请访问：${baseUrl}</p>`
  };
  await sgMail.send(msg as any);
}
