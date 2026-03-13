# Instalily Lead Dashboard - React/Next.js

A professional, production-ready React/Next.js dashboard for managing AI-generated leads from the Instalily lead generation pipeline. Built with TypeScript, Tailwind CSS, and Shadcn/ui components.

## Features

- **Real-time Lead Management**: View, filter, and manage leads from the Python pipeline
- **Inline Editing**: Update lead status and owner directly in the table
- **Sliding Detail Panel**: Comprehensive lead view with contact info, company details, and outreach messages
- **Advanced Filtering**: Filter by lead owner, status, and fit score
- **Sortable Columns**: Click column headers to sort leads
- **Copy-to-Clipboard**: Easy copying of contact details and outreach messages
- **Responsive Design**: Works on desktop and tablet devices
- **TypeScript Throughout**: Full type safety and IntelliSense support

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui (custom built)
- **Icons**: Lucide React
- **Date Formatting**: date-fns
- **Form Management**: React Hook Form (ready for complex forms)

## Project Structure

```
dashboard-nextjs/
├── app/
│   ├── api/
│   │   └── leads/
│   │       └── route.ts          # API endpoints (GET, PATCH)
│   ├── globals.css               # Global styles & Tailwind config
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Main dashboard page
├── components/
│   ├── ui/                       # Shadcn/ui components
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── select.tsx
│   ├── LeadTable.tsx             # Main table with inline editing
│   └── LeadDetailPanel.tsx       # Sliding side panel
├── lib/
│   ├── types.ts                  # TypeScript type definitions
│   └── utils.ts                  # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- The Python pipeline must be set up and have generated `data/leads.json`

### Installation

1. Navigate to the dashboard directory:

```bash
cd dashboard-nextjs
```

2. Install dependencies:

```bash
npm install
```

3. Verify the data file path is correct:

The API route expects `leads.json` at `../data/leads.json` (one level up from the dashboard directory). Ensure your Python pipeline generates the file at `/Users/linus/Desktop/Claude/GTM_agents/data/leads.json`.

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm run start
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## API Routes

### GET /api/leads

Returns all leads from `leads.json`.

**Response:**
```json
{
  "success": true,
  "data": {
    "generated_at": "2026-03-11T22:13:59.921908",
    "pipeline_version": "1.0.0",
    "leads": [...]
  }
}
```

### PATCH /api/leads

Updates a specific lead's CRM data.

**Request:**
```json
{
  "id": "swissqprint-kilian-hintermann",
  "updates": {
    "lead_status": "In Progress",
    "lead_owner": "John Doe",
    "last_interaction_date": "2026-03-12",
    "notes": "Follow up scheduled for next week"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Lead updated successfully",
  "lead": {...}
}
```

## Key Components

### Main Dashboard (`app/page.tsx`)

- Fetches leads from API on mount
- Displays summary metrics (Total Leads, High Fit, Open, In Progress)
- Provides filtering controls
- Manages table and detail panel state

### Lead Table (`components/LeadTable.tsx`)

- Displays leads in a sortable table
- Inline editing for Lead Status and Lead Owner
- Clickable lead names to open detail panel
- Auto-saves changes via API

### Lead Detail Panel (`components/LeadDetailPanel.tsx`)

- Slides in from right side
- Displays complete lead information
- Copy-to-clipboard for contact details and outreach
- Editable CRM fields with save button
- Score breakdown visualization

## Data Flow

```
Python Pipeline (main.py)
    ↓
data/leads.json (flat file)
    ↓
Next.js API Route (/api/leads)
    ↓
React Components (Dashboard)
    ↓
User Updates
    ↓
PATCH /api/leads
    ↓
Updated data/leads.json
```

## Utility Functions

### Industry Classification (`lib/utils.ts`)

Automatically classifies companies into industries based on description keywords:

- Large-Format Printing
- Vehicle Wraps & Fleet Graphics
- Architectural Graphics
- Signage & Graphics
- Digital Printing
- Graphics Solutions
- Distribution & Supply
- Manufacturing
- Print Services

### Fit Score Colors

- **High (≥70)**: Green badge
- **Medium (40-69)**: Yellow badge
- **Low (<40)**: Red badge

### Lead Status Colors

- **Open**: Blue
- **In Progress**: Purple
- **Unqualified**: Gray
- **Closed**: Green

## Customization

### Changing the Data Source

Edit `app/api/leads/route.ts` and update the `LEADS_FILE_PATH` constant:

```typescript
const LEADS_FILE_PATH = path.join(process.cwd(), "..", "data", "leads.json")
```

### Adding New Filters

1. Add filter state to `FilterState` type in `lib/types.ts`
2. Add filter UI in `app/page.tsx`
3. Update filter logic in `filteredLeads` useMemo

### Customizing the Table Columns

Edit `components/LeadTable.tsx` to add/remove columns:

1. Add/remove `<th>` elements in the header
2. Add/remove `<td>` elements in the body
3. Update sort logic if needed

## TypeScript Types

All types are defined in `lib/types.ts`. Key interfaces:

- `Lead`: Complete lead data structure
- `LeadTableRow`: Lead with computed fields (id, industry)
- `FilterState`: Filter state for the dashboard
- `LeadsData`: Top-level data structure from JSON file

## Error Handling

- API errors are caught and displayed to the user
- Failed updates show an alert
- Missing data fields display "—" instead of breaking
- Graceful handling of null/undefined values throughout

## Performance Optimizations

- `useMemo` for filtered leads and metrics calculations
- Debounced inline editing (via blur/Enter key)
- Efficient re-renders with proper key props
- Lazy loading of detail panel content

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2017+ JavaScript features
- CSS Grid and Flexbox

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Ensure `data/leads.json` is accessible (you may need to adjust file paths for production)
4. Deploy

### Other Platforms

Build the static export:

```bash
npm run build
```

Deploy the `.next` directory to your hosting platform.

## Troubleshooting

### API returns 500 error

- Check that `data/leads.json` exists and is valid JSON
- Verify file path in `app/api/leads/route.ts`
- Check server logs for detailed error messages

### Inline editing not saving

- Ensure API route is accessible
- Check browser console for errors
- Verify CRM data structure matches TypeScript types

### Sliding panel not animating

- Ensure `tailwindcss-animate` is installed
- Check that global CSS includes animation utilities
- Verify Tailwind config includes animation plugin

## Future Enhancements

- CSV export of filtered leads
- Bulk edit operations
- Email integration (send outreach directly)
- Real-time updates with WebSockets
- Advanced search across all fields
- Lead assignment workflows
- Activity timeline per lead
- Integration with Clay and LinkedIn APIs (when stubs are activated)

## Contributing

This dashboard was built following TypeScript Standard Style and Next.js best practices. When contributing:

1. Run type checking before committing
2. Follow existing component patterns
3. Add JSDoc comments for complex functions
4. Test inline editing and panel functionality

## License

Private - Instalily Case Study

## Support

For issues or questions, refer to the main project README or contact the development team.
