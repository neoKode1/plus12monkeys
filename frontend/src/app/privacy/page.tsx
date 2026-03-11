import Link from "next/link";

export const metadata = {
  title: "Privacy Policy | +12 Monkeys",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#030303] text-zinc-400 px-6 py-20">
      <div className="max-w-2xl mx-auto space-y-8">
        <Link href="/" className="text-[10px] font-mono uppercase tracking-widest text-zinc-600 hover:text-zinc-400">
          ← Back
        </Link>
        <h1 className="text-2xl font-light text-zinc-200">Privacy Policy</h1>
        <p className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest">
          Effective: March 1, 2026
        </p>

        <section className="space-y-4 text-sm leading-relaxed">
          <h2 className="text-zinc-300 font-medium">1. Information We Collect</h2>
          <p>We collect the minimum data needed to provide the Service:</p>
          <ul className="list-disc list-inside space-y-1 text-zinc-500">
            <li><strong className="text-zinc-400">Email address</strong> — for authentication and account identification</li>
            <li><strong className="text-zinc-400">Usage data</strong> — interaction count, plan type, timestamps</li>
            <li><strong className="text-zinc-400">Payment information</strong> — processed and stored securely by Stripe; we do not store card numbers</li>
          </ul>

          <h2 className="text-zinc-300 font-medium">2. How We Use Your Data</h2>
          <ul className="list-disc list-inside space-y-1 text-zinc-500">
            <li>To authenticate you and manage your account</li>
            <li>To track usage and enforce plan limits</li>
            <li>To process payments via Stripe</li>
            <li>To send transactional emails (magic links, receipts)</li>
          </ul>
          <p>We do not sell your data. We do not send marketing emails.</p>

          <h2 className="text-zinc-300 font-medium">3. Third-Party Services</h2>
          <p>We use the following third-party services that may process your data:</p>
          <ul className="list-disc list-inside space-y-1 text-zinc-500">
            <li><strong className="text-zinc-400">Stripe</strong> — payment processing (<a href="https://stripe.com/privacy" className="underline">privacy policy</a>)</li>
            <li><strong className="text-zinc-400">Anthropic (Claude)</strong> — AI model for agent generation (<a href="https://anthropic.com/privacy" className="underline">privacy policy</a>)</li>
            <li><strong className="text-zinc-400">Resend</strong> — email delivery (<a href="https://resend.com/legal/privacy-policy" className="underline">privacy policy</a>)</li>
            <li><strong className="text-zinc-400">MongoDB Atlas</strong> — database hosting</li>
            <li><strong className="text-zinc-400">Vercel</strong> — frontend hosting</li>
            <li><strong className="text-zinc-400">Railway</strong> — backend hosting</li>
          </ul>

          <h2 className="text-zinc-300 font-medium">4. Data Retention</h2>
          <p>Account data is retained while your account is active. Magic link tokens are automatically deleted after expiration. You may request deletion of your account and data by contacting us.</p>

          <h2 className="text-zinc-300 font-medium">5. Security</h2>
          <p>We use industry-standard security measures including encrypted connections (HTTPS), secure cookie handling, and JWT-based authentication. Payment data is handled entirely by Stripe and never touches our servers.</p>

          <h2 className="text-zinc-300 font-medium">6. Cookies</h2>
          <p>We use a single session cookie (<code className="text-zinc-500">twelve_monkeys_session</code>) for authentication. We do not use tracking cookies or analytics cookies.</p>

          <h2 className="text-zinc-300 font-medium">7. Your Rights</h2>
          <p>You have the right to: access your data, request correction, request deletion, and export your data. Contact us to exercise any of these rights.</p>

          <h2 className="text-zinc-300 font-medium">8. Children</h2>
          <p>The Service is not directed to children under 13. We do not knowingly collect data from children.</p>

          <h2 className="text-zinc-300 font-medium">9. Changes</h2>
          <p>We may update this policy. Material changes will be communicated via email. Continued use constitutes acceptance.</p>

          <h2 className="text-zinc-300 font-medium">10. Contact</h2>
          <p>Privacy questions? Email <a href="mailto:1deeptechnology@gmail.com" className="text-zinc-300 underline">1deeptechnology@gmail.com</a></p>
        </section>

        <div className="pt-8 border-t border-zinc-900 text-[9px] font-mono text-zinc-700 uppercase tracking-widest">
          +12 Monkeys © 2025. All Rights Reserved.
        </div>
      </div>
    </div>
  );
}

