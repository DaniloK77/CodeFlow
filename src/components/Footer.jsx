import { Github, Twitter, Linkedin, Mail } from "lucide-react";

const footerLinks = {
  Product: ["Features", "Pricing", "Security", "Roadmap", "Changelog"],
  Company: ["About", "Blog", "Careers", "Press", "Partners"],
  Resources: [
    "Documentation",
    "Help Center",
    "Community",
    "API Reference",
    "Status",
  ],
  Legal: ["Privacy", "Terms", "Cookie Policy", "Licenses", "Compliance"],
};

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950/60 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 lg:py-16">

        {/* Main footer */}
        <div className="hidden sm:grid sm:grid-cols-3 lg:grid-cols-6 gap-8 lg:gap-12 mb-10">

          {/* Brand */}
          <div className="col-span-1 sm:col-span-3 lg:col-span-2 text-center sm:text-left">

            <div className="flex items-center justify-center sm:justify-start space-x-2 mb-4">
              <img
                src="/logo.png"
                alt="CodeFlow Logo"
                className="w-7 h-7 sm:w-9 sm:h-9"
              />

              <span className="text-lg sm:text-xl font-bold">
                <span className="text-white">Code</span>
                <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  Flow
                </span>
              </span>
            </div>

            <p className="text-gray-400 mb-6 max-w-xs mx-auto sm:mx-0 text-sm sm:text-base leading-relaxed">
              Transform your workflow with AI-powered tools and automation.
              Built for modern teams and developers.
            </p>

            {/* Social icons */}
            <div className="flex justify-center sm:justify-start space-x-4">

              <a
                href="#"
                className="p-2.5 bg-slate-800 rounded-lg hover:bg-slate-700 hover:scale-110 transition-all duration-200"
              >
                <Twitter className="w-5 h-5 text-gray-300" />
              </a>

              <a
                href="#"
                className="p-2.5 bg-slate-800 rounded-lg hover:bg-slate-700 hover:scale-110 transition-all duration-200"
              >
                <Github className="w-5 h-5 text-gray-300" />
              </a>

              <a
                href="#"
                className="p-2.5 bg-slate-800 rounded-lg hover:bg-slate-700 hover:scale-110 transition-all duration-200"
              >
                <Linkedin className="w-5 h-5 text-gray-300" />
              </a>

              <a
                href="#"
                className="p-2.5 bg-slate-800 rounded-lg hover:bg-slate-700 hover:scale-110 transition-all duration-200"
              >
                <Mail className="w-5 h-5 text-gray-300" />
              </a>

            </div>
          </div>

          {/* Footer links */}
          <div className="sm:col-span-3 lg:col-span-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-8">

              {Object.entries(footerLinks).map(([category, links]) => (
                <div key={category}>

                  <h3 className="font-semibold text-white mb-4 text-sm sm:text-base">
                    {category}
                  </h3>

                  <ul className="space-y-2.5">

                    {links.map((link) => (
                      <li key={link}>
                        <a
                          href="#"
                          className="text-gray-400 hover:text-white transition-colors duration-200 text-sm"
                        >
                          {link}
                        </a>
                      </li>
                    ))}

                  </ul>

                </div>
              ))}

            </div>
          </div>

        </div>

        {/* Bottom bar */}
        <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">

          <p className="text-gray-400 text-xs sm:text-sm text-center sm:text-left">
  © {new Date().getFullYear()} CodeFlow. All rights reserved.
</p>
          <div className="flex items-center space-x-5 text-xs sm:text-sm">

            <a
              href="#"
              className="text-gray-400 hover:text-white transition-colors duration-200"
            >
              Privacy Policy
            </a>

            <a
              href="#"
              className="text-gray-400 hover:text-white transition-colors duration-200"
            >
              Terms of Service
            </a>

            <a
              href="#"
              className="text-gray-400 hover:text-white transition-colors duration-200"
            >
              Cookie Settings
            </a>

          </div>

        </div>

      </div>
    </footer>
  );
}