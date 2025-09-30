# Traceback - Campus Lost & Found

A modern, responsive web application for tracking lost and found items on campus.

## Features

- 📱 **Full-screen responsive design** - Works seamlessly on all devices
- 🎨 **Modern monochrome UI** - Clean, professional design with black/white/gray theme
- 🔍 **Smart matching system** - Connects lost items with found items
- 🏫 **Campus-wide coverage** - Covers all campus buildings and areas
- 🔒 **Secure authentication** - Student account verification system
- ⚡ **Real-time updates** - Instant notifications for matches

## Tech Stack

- **Framework**: Next.js 14
- **Styling**: Tailwind CSS
- **Authentication**: JWT-based system
- **UI Components**: Custom React components
- **State Management**: React hooks

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/akshitha1024/traceback.git
cd traceback
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3001](http://localhost:3001) in your browser.

## Project Structure

```
traceback/
├── app/                    # Next.js app directory
│   ├── dashboard/         # Dashboard page
│   ├── login/            # Authentication pages
│   ├── signup/           
│   ├── found/            # Found items page
│   ├── lost/             # Lost items page
│   └── report/           # Report item page
├── components/            # Reusable components
│   ├── Navbar.js         # Navigation bar
│   ├── Sidebar.js        # Sidebar navigation
│   ├── ItemCard.js       # Item display card
│   └── Protected.js      # Authentication wrapper
├── data/                 # Mock data
└── public/               # Static assets
```

## Key Pages

- **Landing Page**: Full-screen hero with call-to-action buttons
- **Dashboard**: Overview of matches and recent items
- **Authentication**: Modern login/signup with glass morphism design
- **Item Lists**: Browse lost and found items with filtering
- **Report**: Submit new lost or found items

## Design Features

- **Glass Morphism**: Subtle backdrop blur effects
- **Responsive Typography**: Scales from mobile to desktop
- **Hover Animations**: Smooth transitions and transforms
- **Consistent Spacing**: Systematic design system
- **Accessibility**: Proper contrast ratios and focus states

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Contact

**Developer**: Akshitha  
**Repository**: https://github.com/akshitha1024/traceback

---

Built with ❤️ for campus communities