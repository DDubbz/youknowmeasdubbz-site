    let allGigs = [];
    let currentFilter = 'upcoming';
    let visibleCount = 10;
    const PER_PAGE = 10;

    async function loadGigs() {
      try {
        const res = await fetch('/api/gigs.json?limit=50');
        if (res.ok) {
          allGigs = await res.json();
        } else {
          throw new Error('API not ready');
        }
      } catch (e) {
        console.log('Gig API not ready, using static fallbacks');
        loadStaticGigs();
        return;
      }
      renderGigs();
    }

    function loadStaticGigs() {
      allGigs = [
        {
          id: '1',
          title: 'Avacado Cantina — Saturday Sessions',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-09-12',
          startTime: '20:00',
          endTime: '23:00',
          status: 'booked',
          fee: 300,
          isRecurring: true,
          recurringPattern: 'weekly-friday',
          notes: 'Weekly Saturday residency. Cash paid by Christian (Asst GM) at end of night.'
        },
        {
          id: '2',
          title: 'FLAVAR Call Collect — September Edition',
          venue: 'French Grille',
          address: '427 Northwood Rd, West Palm Beach, FL 33407',
          date: '2026-09-27',
          startTime: '15:00',
          endTime: '23:00',
          status: 'booked',
          isRecurring: true,
          recurringPattern: 'monthly-sunday',
          notes: 'Monthly Sunday day party. Doors 3 PM. Outdoor rotation + indoor karaoke + Suede Suite vinyl.'
        },
        {
          id: '3',
          title: 'Avacado Cantina — Saturday Sessions',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-09-19',
          startTime: '20:00',
          endTime: '23:00',
          status: 'booked',
          fee: 300,
          isRecurring: true,
          recurringPattern: 'weekly-friday'
        },
        {
          id: '4',
          title: 'Avacado Cantina — Saturday Sessions',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-09-26',
          startTime: '20:00',
          endTime: '23:00',
          status: 'booked',
          fee: 300,
          isRecurring: true,
          recurringPattern: 'weekly-friday'
        },
        {
          id: '5',
          title: 'FLAVAR Call Collect — October Edition',
          venue: 'French Grille',
          address: '427 Northwood Rd, West Palm Beach, FL 33407',
          date: '2026-10-25',
          startTime: '15:00',
          endTime: '23:00',
          status: 'booked',
          isRecurring: true,
          recurringPattern: 'monthly-sunday'
        },
        {
          id: '6',
          title: 'Avacado Cantina — Saturday Sessions',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-10-03',
          startTime: '20:00',
          endTime: '23:00',
          status: 'booked',
          fee: 300,
          isRecurring: true,
          recurringPattern: 'weekly-friday'
        },
        {
          id: '7',
          title: 'Avacado Cantina — Saturday Sessions',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-10-10',
          startTime: '20:00',
          endTime: '23:00',
          status: 'booked',
          fee: 300,
          isRecurring: true,
          recurringPattern: 'weekly-friday'
        },
        {
          id: '8',
          title: 'Avacado Cantina — DJ Gotti Covering',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-10-17',
          startTime: '20:00',
          endTime: '23:00',
          status: 'booked',
          fee: 300,
          notes: 'CONFLICT: Overlaps with Benjamin School. DJ Gotti covering (1-728-201-4418).'
        },
        {
          id: '9',
          title: 'Palm House Hotel — Venue Walkthrough',
          venue: 'Palm House Hotel — The Bar',
          address: '160 Royal Palm Way, Palm Beach, FL 33480',
          date: '2026-10-27',
          startTime: '14:00',
          endTime: '17:00',
          status: 'booked',
          fee: 390,
          notes: 'Venue walkthrough for Nov 7 booked gig. Gear: speaker, DJ booth, controller.'
        },
        {
          id: '10',
          title: 'Palm House Hotel — The Bar',
          venue: 'Palm House Hotel — The Bar',
          address: '160 Royal Palm Way, Palm Beach, FL 33480',
          date: '2026-11-07',
          startTime: '16:00',
          endTime: '19:00',
          status: 'booked',
          fee: 390,
          notes: 'Booked gig. Gear: speaker, DJ booth, controller. Contact: +1 561-858-1600'
        },
        {
          id: '11',
          title: 'Camelot Yacht Club — All White Party',
          venue: 'Camelot Yacht Club',
          address: 'Unknown',
          date: '2026-09-06',
          startTime: '21:00',
          endTime: '04:15',
          status: 'actual',
          fee: 0,
          notes: 'Opening 9-11:20 PM, Closing 1:08-4:15 AM. DJ Don Hot headliner middle. 125 tracks, 6.88h.'
        },
        {
          id: '12',
          title: 'Avacado Cantina — Saturday Session',
          venue: 'Avacado Cantina',
          address: '11701 Lake Victoria Gardens Ave, Ste 4105, Palm Beach Gardens, FL 33410',
          date: '2026-09-05',
          startTime: '20:00',
          endTime: '23:00',
          status: 'actual',
          fee: 300,
          notes: '91 tracks played. Dancehall/afrobeats peak at 21:52-22:10. Recording: Avacado Cantina - 9-5-26.wav'
        }
      ];
      renderGigs();
    }

    function renderGigs() {
      const container = document.getElementById('gigs-list');
      if (!container) return;

      let filtered = [];
      const now = new Date();
      const todayMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);

      if (currentFilter === 'upcoming') {
        filtered = allGigs.filter(g => {
          const d = new Date(g.date);
          const gMidnight = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0);
          return gMidnight >= todayMidnight;
        });
      } else if (currentFilter === 'past') {
        filtered = allGigs.filter(g => {
          const d = new Date(g.date);
          const gMidnight = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0);
          return gMidnight < todayMidnight;
        });
      } else if (currentFilter === 'residencies') {
        filtered = allGigs.filter(g => g.isRecurring);
      } else if (currentFilter === 'flavar') {
        filtered = allGigs.filter(g => g.title.toLowerCase().includes('flavar'));
      }

      filtered.sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return currentFilter === 'past' ? dateB - dateA : dateA - dateB;
      });

      const visible = filtered.slice(0, visibleCount);

      if (!visible.length) {
        container.innerHTML = `
          <div class="panel" style="padding: var(--space-12); text-align: center;">
            <p style="color: var(--color-text-muted);">No events found for this filter.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = visible.map((gig, i) => {
        const startTime12 = gig.startTime ? formatTime12h(gig.startTime) : '';
        const endTime12 = gig.endTime ? formatTime12h(gig.endTime) : '';
        return `
        <article class="gig-card animate-fade-in-up" style="animation-delay: ${i * 80}ms;" data-status="${gig.status}" role="listitem">
          <div class="gig-date">
            <div class="gig-day">${new Date(gig.date).getDate()}</div>
            <div class="gig-month">${new Date(gig.date).toLocaleString('en-US', { month: 'short' }).toUpperCase()}</div>
          </div>
          <div class="gig-info">
            <h3>${gig.title}</h3>
            <p class="gig-venue">${gig.venue}</p>
            <p class="gig-location">${gig.address}</p>
            <div class="gig-meta">
              <span class="gig-time">${startTime12}${endTime12 ? ' – ' + endTime12 : ''}</span>
              ${gig.isRecurring ? '<span>🔁 ' + gig.recurringPattern + '</span>' : ''}
            </div>
          </div>
          <div class="gig-actions">
            <button class="btn btn-calendar" type="button" data-gig-title="${gig.title.replace(/'/g, '')}" data-gig-date="${gig.date}" data-gig-start="${gig.startTime || ''}" data-gig-end="${gig.endTime || ''}" data-gig-venue="${(gig.venue || '').replace(/'/g, '')}" data-gig-address="${(gig.address || '').replace(/'/g, '')}" title="Add to Calendar" aria-label="Add ${gig.title} to calendar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              <span>Remind Me</span>
            </button>
          </div>
        </article>
      `}).join('');

      container.querySelectorAll('.btn-calendar').forEach(btn => {
        btn.addEventListener('click', () => {
          addToCalendar(
            btn.dataset.gigTitle,
            btn.dataset.gigDate,
            btn.dataset.gigStart,
            btn.dataset.gigEnd,
            btn.dataset.gigVenue,
            btn.dataset.gigAddress
          );
        });
      });

      const loadMoreBtn = document.getElementById('load-more-gigs');
      if (loadMoreBtn) {
        loadMoreBtn.style.display = visible.length >= filtered.length ? 'none' : 'block';
      }
    }

    function filterGigs(filter) {
      currentFilter = filter;
      visibleCount = PER_PAGE;
      renderGigs();

      document.querySelectorAll('#gig-filters .filter-btn').forEach(btn => {
        const isActive = btn.dataset.filter === filter;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', isActive);
      });
    }

    function formatTime12h(time24) {
      if (!time24) return '';
      const [hours, minutes] = time24.split(':').map(Number);
      const period = hours >= 12 ? 'PM' : 'AM';
      const hours12 = hours % 12 || 12;
      return `${hours12}:${String(minutes).padStart(2, '0')} ${period}`;
    }

    function addToCalendar(title, date, startTime, endTime, venue, location) {
      const dtStart = date.replace(/-/g, '') + 'T' + (startTime || '00:00').replace(':', '') + '00';
      const dtEnd = date.replace(/-/g, '') + 'T' + (endTime || '23:59').replace(':', '') + '00';
      const icsContent = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Dubbz Studio//Event Reminder//EN',
        'BEGIN:VEVENT',
        `UID:${Date.now()}@dubbz.studio`,
        `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').split('.')[0]}Z`,
        `DTSTART:${dtStart}`,
        `DTEND:${dtEnd}`,
        `SUMMARY:${title}`,
        `DESCRIPTION:${title} — ${venue || ''} ${location || ''}`.trim(),
        `LOCATION:${venue || ''}${location ? ', ' + location : ''}`.trim(),
        'END:VEVENT',
        'END:VCALENDAR'
      ].join('\r\n');

      const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-reminder.ics`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    function loadMoreGigs() {
      visibleCount += PER_PAGE;
      renderGigs();
    }

    document.addEventListener('DOMContentLoaded', () => {
      loadGigs();

      document.querySelectorAll('#gig-filters .filter-btn').forEach(btn => {
        btn.addEventListener('click', () => filterGigs(btn.dataset.filter));
      });

      document.getElementById('load-more-gigs')?.addEventListener('click', loadMoreGigs);
    });