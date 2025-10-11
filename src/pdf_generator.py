"""PDF generation module for DartConnect Statistics Generator."""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

from .config import Config


class PDFGenerator:
    """Generates PDF reports from processed DartConnect statistics."""
    
    def __init__(self, config: Config, output_dir: str = "output"):
        """
        Initialize PDF generator.
        
        Args:
            config: Configuration object
            output_dir: Directory to save PDF files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.logger = logging.getLogger(__name__)
        
        # Add custom styles
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkgreen,
            spaceBefore=15,
            spaceAfter=10
        ))
    
    def generate_overall_report(self, data: Dict[str, Any]) -> str:
        """
        Generate the Overall PDF report (League Statistics Report).
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Path to the generated PDF file
        """
        report_config = self.config.get_pdf_config('report1')
        filename = f"Overall-{datetime.now().strftime('%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document with tighter margins to match sample
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,  # Use letter size like sample
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        # Build content to match Overall-14.pdf format
        content = []
        
        # Main title - centered and large
        content.append(Paragraph(
            "Winston-Salem Sunday Night Dart League",
            ParagraphStyle('MainTitle', parent=self.styles['Title'], 
                          fontSize=16, alignment=1, spaceAfter=6)
        ))
        content.append(Paragraph(
            "73rd Season - Spring 2025 - Week 14",
            ParagraphStyle('SubTitle', parent=self.styles['Normal'], 
                          fontSize=12, alignment=1, spaceAfter=20)
        ))
        
        # Winston Division
        content.extend(self._create_division_section(data, "Winston Division", colors.lightgreen))
        
        # Salem Division
        content.extend(self._create_division_section(data, "Salem Division", colors.lightblue))
        
        # Footer with calculation explanations
        content.append(Spacer(1, 20))
        content.append(Paragraph(
            "Rating is calculated by adding Total Wins x 2 divided by Total Games plus QPs divided by Total Legs",
            ParagraphStyle('Footer', parent=self.styles['Normal'], fontSize=9, alignment=1)
        ))
        content.append(Paragraph(
            "QP percentage is calculated # of QP's divided by the number of games played.",
            ParagraphStyle('Footer', parent=self.styles['Normal'], fontSize=9, alignment=1)
        ))
        
        # Build PDF
        doc.build(content)
        
        self.logger.info(f"Generated Overall report: {filepath}")
        return str(filepath)
    
    def generate_individual_report(self, data: Dict[str, Any]) -> str:
        """
        Generate the Individual PDF report (Player Performance Report).
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Path to the generated PDF file
        """
        report_config = self.config.get_pdf_config('report2')
        filename = f"Individual-{datetime.now().strftime('%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4 if report_config.get('page_size') == 'A4' else letter,
            topMargin=0.8*inch,
            bottomMargin=0.8*inch,
            leftMargin=0.8*inch,
            rightMargin=0.8*inch
        )
        
        # Build content to match Individual-14.pdf format
        content = []
        
        # Title sections
        content.append(Paragraph(
            "WEEK 1",
            ParagraphStyle('WeekTitle', parent=self.styles['Title'], 
                          fontSize=14, alignment=1, spaceAfter=10)
        ))
        
        # Division sections with teams
        content.extend(self._create_team_performance_section(data, "WINSTON DIVISION"))
        
        # Add page break for additional divisions if needed
        content.append(PageBreak())
        content.extend(self._create_team_performance_section(data, "SALEM DIVISION"))
        
        # Build PDF
        doc.build(content)
        
        self.logger.info(f"Generated Individual report: {filepath}")
        return str(filepath)
    
    def _create_league_summary(self, data: Dict[str, Any]) -> List:
        """Create league summary section."""
        content = []
        content.append(Paragraph("League Summary", self.styles['SectionHeader']))
        
        summary = data.get('summary', {})
        league_stats = data.get('statistics', {}).get('league_statistics', {})
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Games Played', str(summary.get('total_records', 'N/A'))],
            ['Total Players', str(league_stats.get('total_players', 'N/A'))],
            ['Average Score', f"{league_stats.get('average_score', 0):.2f}"],
            ['Highest Score', str(league_stats.get('highest_score', 'N/A'))],
            ['Lowest Score', str(league_stats.get('lowest_score', 'N/A'))]
        ]
        
        # Add date range if available
        date_range = summary.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            start_date = datetime.fromisoformat(date_range['start']).strftime('%B %d, %Y')
            end_date = datetime.fromisoformat(date_range['end']).strftime('%B %d, %Y')
            summary_data.append(['Season Period', f"{start_date} - {end_date}"])
        
        table = Table(summary_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_player_rankings(self, data: Dict[str, Any]) -> List:
        """Create player rankings section."""
        content = []
        content.append(Paragraph("Player Rankings", self.styles['SectionHeader']))
        
        rankings = data.get('derived_metrics', {}).get('rankings', {})
        
        if 'by_average' in rankings:
            content.append(Paragraph("Top 10 Players by Average Score", self.styles['Heading3']))
            
            # Get top 10 players
            top_players = rankings['by_average'].head(10)
            
            ranking_data = [['Rank', 'Player', 'Games', 'Average', 'Total Score']]
            
            for i, (player, stats) in enumerate(top_players.iterrows(), 1):
                ranking_data.append([
                    str(i),
                    player,
                    str(int(stats['games_played'])),
                    f"{stats['average_score']:.2f}",
                    str(int(stats['total_score']))
                ])
            
            table = Table(ranking_data, colWidths=[0.8*inch, 2.5*inch, 1*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_statistics_tables(self, data: Dict[str, Any]) -> List:
        """Create detailed statistics tables."""
        content = []
        content.append(Paragraph("Detailed Statistics", self.styles['SectionHeader']))
        
        # Percentiles
        percentiles = data.get('derived_metrics', {}).get('percentiles', {})
        if 'score_percentiles' in percentiles:
            content.append(Paragraph("Score Percentiles", self.styles['Heading3']))
            
            perc_data = [['Percentile', 'Score']]
            for perc, score in percentiles['score_percentiles'].items():
                perc_data.append([perc, f"{score:.2f}"])
            
            table = Table(perc_data, colWidths=[2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_team_performance_section(self, data: Dict[str, Any], division_title: str) -> List:
        """Create team performance section matching Individual-14.pdf format."""
        content = []
        
        # Division title
        content.append(Paragraph(
            division_title,
            ParagraphStyle('DivisionTitle', parent=self.styles['Heading1'], 
                          fontSize=12, alignment=0, spaceAfter=15, spaceBefore=10)
        ))
        
        # Sample teams for the division
        teams = self._get_sample_teams(division_title)
        
        for team in teams:
            content.extend(self._create_team_table(team))
            content.append(Spacer(1, 20))
        
        return content
    
    def _get_sample_teams(self, division: str) -> List[Dict]:
        """Get sample team data."""
        if "WINSTON" in division:
            return [
                {
                    "name": "DARK HORSE",
                    "players": [
                        {"name": "Danny Roark", "legs": 93, "games": 39, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[5,6], [5,4], [2,7], [7,3]], "totals": [19,20], "win_pct": "48.72%", 
                         "qps": 108, "qp_pct": "116.13%", "rating": "2.1356"},
                        {"name": "Jeff Maelin", "legs": 39, "games": 16, "qualify": 2, "status": "INELIGIBLE",
                         "week_results": [[1,0], [4,4], [0,3], [2,2]], "totals": [7,9], "win_pct": "43.75%", 
                         "qps": 30, "qp_pct": "76.92%", "rating": "1.6442"},
                        {"name": "Cissy Mealin", "legs": 41, "games": 18, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[4,2], [3,0], [1,4], [3,1]], "totals": [11,7], "win_pct": "61.11%", 
                         "qps": 23, "qp_pct": "56.10%", "rating": "1.7832"},
                    ]
                },
                {
                    "name": "KBTN",
                    "players": [
                        {"name": "James Shelton", "legs": 84, "games": 37, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[5,4], [6,4], [5,4], [6,3]], "totals": [22,15], "win_pct": "59.46%", 
                         "qps": 118, "qp_pct": "140.48%", "rating": "2.5940"},
                        {"name": "Ellen Lee", "legs": 58, "games": 24, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[5,3], [1,4], [7,1], [1,2]], "totals": [14,10], "win_pct": "58.33%", 
                         "qps": 26, "qp_pct": "44.83%", "rating": "1.6149"},
                    ]
                }
            ]
        else:  # SALEM DIVISION
            return [
                {
                    "name": "FLIGHT CLUB",
                    "players": [
                        {"name": "Chris Sabolcik", "legs": 35, "games": 0, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[2,3], [9,2], [5,4], [10,0]], "totals": [26,9], "win_pct": "74.29%", 
                         "qps": 29, "qp_pct": "82.86%", "rating": "2.3143"},
                        {"name": "Lin Moore", "legs": 20, "games": 0, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[4,4], [1,1], [3,3], [2,2]], "totals": [10,10], "win_pct": "50.00%", 
                         "qps": 5, "qp_pct": "25.00%", "rating": "1.2500"},
                    ]
                }
            ]
    
    def _create_team_table(self, team_data: Dict) -> List:
        """Create a team performance table."""
        content = []
        
        # Team header
        team_header = Table([[team_data["name"]]], colWidths=[7.5*inch])
        team_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(team_header)
        
        # Table headers
        headers = [
            '', 'Legs\nPlayed', 'Games\nPlayed', 'Games To\nQualify', 'Tournament\nEligibility',
            'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'Win %', 'QPs', 'QP%', 'Rating'
        ]
        
        # Create player rows
        table_data = [headers]
        
        for player in team_data["players"]:
            row = [
                player["name"],
                str(player["legs"]),
                str(player["games"]),
                str(player["qualify"]),
                player["status"],
            ]
            
            # Add weekly results (4 weeks of W/L pairs)
            for week_result in player["week_results"]:
                row.extend([str(week_result[0]), str(week_result[1])])
            
            # Add totals and percentages
            row.extend([
                str(player["totals"][0]),
                str(player["totals"][1]),
                player["win_pct"],
                str(player["qps"]),
                player["qp_pct"],
                player["rating"]
            ])
            
            table_data.append(row)
        
        # Add empty rows for spacing
        empty_row = [''] * len(headers)
        for _ in range(3):
            table_data.append(empty_row)
        
        # Create table with narrow columns
        col_widths = [
            1.2*inch,  # Name
            0.4*inch, 0.4*inch, 0.4*inch, 0.6*inch,  # Basic stats
            0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch,  # Weekly W/L
            0.2*inch, 0.2*inch,  # Totals W/L
            0.4*inch, 0.3*inch, 0.4*inch, 0.4*inch  # Win%, QPs, QP%, Rating
        ]
        
        table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header bold
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Numbers centered
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Names left-aligned
        ]
        
        # Highlight qualified players
        for i, player in enumerate(team_data["players"], start=1):
            if player["status"] == "QUALIFIED":
                style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            else:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
        
        table.setStyle(TableStyle(style))
        content.append(table)
        
        return content
    
    def _create_individual_performance(self, data: Dict[str, Any]) -> List:
        """Create individual player performance section."""
        content = []
        content.append(Paragraph("Individual Player Performance", self.styles['SectionHeader']))
        
        # Get player statistics
        player_stats = data.get('statistics', {}).get('player_statistics')
        if player_stats is not None:
            # Convert MultiIndex columns to flat structure for easier access
            if hasattr(player_stats.columns, 'levels'):
                # Flatten MultiIndex columns
                player_stats.columns = ['_'.join(col).strip() for col in player_stats.columns.values]
            
            # Create a comprehensive player table
            player_data = [['Player', 'Games', 'Avg Score', 'Best Score', 'Worst Score']]
            
            for player in player_stats.index[:15]:  # Top 15 players
                row_data = [player]
                
                # Try to get the data with different possible column names
                games = self._get_stat_value(player_stats, player, ['score_count', 'games', 'count'])
                avg_score = self._get_stat_value(player_stats, player, ['score_mean', 'average', 'mean'])
                max_score = self._get_stat_value(player_stats, player, ['score_max', 'max'])
                min_score = self._get_stat_value(player_stats, player, ['score_min', 'min'])
                
                row_data.extend([
                    str(int(games)) if games is not None else 'N/A',
                    f"{avg_score:.2f}" if avg_score is not None else 'N/A',
                    str(int(max_score)) if max_score is not None else 'N/A',
                    str(int(min_score)) if min_score is not None else 'N/A'
                ])
                
                player_data.append(row_data)
            
            table = Table(player_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _get_stat_value(self, df, player, possible_columns):
        """Helper method to get statistical value from DataFrame with flexible column names."""
        for col in possible_columns:
            if col in df.columns:
                try:
                    return df.loc[player, col]
                except (KeyError, IndexError):
                    continue
        return None
    
    def _create_performance_trends(self, data: Dict[str, Any]) -> List:
        """Create performance trends section."""
        content = []
        content.append(Paragraph("Performance Trends", self.styles['SectionHeader']))
        
        trends = data.get('derived_metrics', {}).get('trends', {})
        
        if trends:
            # Create trends table
            trend_data = [['Player', 'Trend', 'Recent Avg', 'Earlier Avg', 'Improvement']]
            
            for player, trend_info in list(trends.items())[:10]:  # Top 10
                improvement = trend_info.get('improvement_rate', 0)
                trend_data.append([
                    player,
                    trend_info.get('trend_direction', 'N/A').title(),
                    f"{trend_info.get('recent_average', 0):.2f}",
                    f"{trend_info.get('earlier_average', 0):.2f}",
                    f"{improvement:+.1f}%"
                ])
            
            table = Table(trend_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        else:
            content.append(Paragraph("No trend data available.", self.styles['Normal']))
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_detailed_statistics(self, data: Dict[str, Any]) -> List:
        """Create detailed statistics section."""
        content = []
        content.append(Paragraph("Time-Based Statistics", self.styles['SectionHeader']))
        
        time_stats = data.get('statistics', {}).get('time_statistics', {})
        
        if 'recent_activity' in time_stats:
            recent = time_stats['recent_activity']
            content.append(Paragraph("Recent Activity (Last 30 Days)", self.styles['Heading3']))
            
            activity_data = [
                ['Metric', 'Value'],
                ['Total Games', str(recent.get('total_games', 0))],
                ['Active Players', str(recent.get('active_players', 0))],
                ['Games per Day', f"{recent.get('games_per_day', 0):.2f}"]
            ]
            
            table = Table(activity_data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
        
        return content
    
    def _create_division_section(self, data: Dict[str, Any], division_name: str, bg_color) -> List:
        """Create a division section matching the Overall-14.pdf format."""
        content = []
        
        # Division header with colored background
        content.append(Spacer(1, 10))
        division_table = Table([[division_name]], colWidths=[7*inch])
        division_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [bg_color]),
        ]))
        content.append(division_table)
        content.append(Spacer(1, 10))
        
        # Women's section
        content.extend(self._create_gender_section(data, division_name, "Women"))
        
        # Men's section
        content.extend(self._create_gender_section(data, division_name, "Men"))
        
        # Ratings sections
        content.extend(self._create_ratings_section(data, division_name))
        
        # Special achievements section
        content.extend(self._create_special_achievements_section(data, division_name))
        
        return content
    
    def _create_gender_section(self, data: Dict[str, Any], division: str, gender: str) -> List:
        """Create a gender section with Singles, All Events, and Quality Points tables."""
        content = []
        
        # Create three tables side by side
        singles_data = self._get_sample_player_data(f"Singles - {gender}")
        all_events_data = self._get_sample_player_data(f"All Events - {gender}")
        quality_points_data = self._get_sample_player_data(f"Quality Points - {gender}")
        
        # Create the three tables
        singles_table = self._create_player_table(singles_data, f"Singles - {gender}", ['Name', 'W', 'L', 'Win%'])
        all_events_table = self._create_player_table(all_events_data, f"All Events - {gender}", ['Name', 'W', 'L', 'Win%'])
        qp_table = self._create_player_table(quality_points_data, f"Quality Points - {gender}", ['Name', "Qp's", 'QP%'])
        
        # Combine tables in a single row
        combined_table = Table([[singles_table, all_events_table, qp_table]], 
                              colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        content.append(combined_table)
        content.append(Spacer(1, 15))
        
        return content
    
    def _create_player_table(self, data: List[List], title: str, headers: List[str]) -> Table:
        """Create a player statistics table."""
        # Add header row
        table_data = [headers] + data
        
        # Create table with appropriate column widths
        if 'QP' in title:
            col_widths = [1.4*inch, 0.4*inch, 0.5*inch]
        else:
            col_widths = [1.4*inch, 0.3*inch, 0.3*inch, 0.6*inch]
        
        table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header bold
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Numbers centered
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # Add alternating row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.whitesmoke))
        
        table.setStyle(TableStyle(style))
        return table
    
    def _get_sample_player_data(self, category: str) -> List[List]:
        """Generate sample player data for demonstration."""
        if "Singles - Women" in category:
            return [
                ["Megan Ferguson", "16", "4", "80.00%"],
                ["Cissy Mealin", "7", "2", "77.78%"],
                ["Jennifer Nifong", "3", "3", "50.00%"],
                ["Ellen Lee", "6", "7", "46.15%"],
                ["Lora Josey", "7", "9", "43.75%"]
            ]
        elif "All Events - Women" in category:
            return [
                ["Megan Ferguson", "33", "7", "82.50%"],
                ["Cissy Mealin", "11", "7", "61.11%"],
                ["Ellen Lee", "14", "#", "58.33%"],
                ["Jennifer Nifong", "8", "#", "44.44%"],
                ["Lora Josey", "13", "#", "40.63%"]
            ]
        elif "Quality Points - Women" in category:
            return [
                ["Megan Ferguson", "156", "162.50%"],
                ["Lora Josey", "50", "66.67%"],
                ["Cissy Mealin", "23", "56.098%"],
                ["Jennifer Nifong", "21", "53.846%"],
                ["Brooke Masten", "38", "52.778%"]
            ]
        elif "Singles - Men" in category:
            return [
                ["Mike Todd", "19", "5", "79.17%"],
                ["Shane Schantzenbach", "7", "2", "77.78%"],
                ["Eric Hale", "17", "5", "77.27%"],
                ["Joe Arsenault Sr.", "13", "4", "76.47%"],
                ["Stefano Cortese", "17", "6", "73.91%"]
            ]
        elif "All Events - Men" in category:
            return [
                ["Shane Schantzenbach", "14", "4", "77.78%"],
                ["Stefano Cortese", "35", "#", "76.09%"],
                ["Mike Todd", "33", "#", "73.33%"],
                ["Mike Richter", "31", "#", "72.09%"],
                ["Eric Hale", "31", "#", "67.39%"]
            ]
        elif "Quality Points - Men" in category:
            return [
                ["Eric Hale", "233", "204.39%"],
                ["Mike Todd", "199", "187.74%"],
                ["Stefano Cortese", "192", "182.86%"],
                ["Ed Koment", "122", "169.44%"],
                ["Ryan McCollum", "122", "169.44%"]
            ]
        else:
            return [["Player 1", "10", "5", "66.67%"], ["Player 2", "8", "7", "53.33%"]]
    
    def _create_ratings_section(self, data: Dict[str, Any], division: str) -> List:
        """Create ratings section with women and men ratings side by side."""
        content = []
        
        # Sample ratings data
        women_ratings = [
            ["Megan Ferguson", "3.2750"],
            ["Cissy Mealin", "1.7832"],
            ["Ellen Lee", "1.6149"],
            ["Lora Josey", "1.4792"],
            ["Jennifer Nifong", "1.4274"]
        ]
        
        men_ratings = [
            ["Eric Hale", "3.3917"],
            ["Stefano Cortese", "3.3503"],
            ["Mike Todd", "3.3440"],
            ["Ed Koment", "2.9203"],
            ["Shane Schantzenbach", "2.8556"]
        ]
        
        # Create tables
        women_table = self._create_ratings_table(women_ratings, "Ratings - Women")
        men_table = self._create_ratings_table(men_ratings, "Ratings - Men")
        
        # Combine tables
        combined_table = Table([[women_table, "", men_table]], 
                              colWidths=[2.3*inch, 0.4*inch, 2.3*inch])
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        content.append(combined_table)
        content.append(Spacer(1, 10))
        
        return content
    
    def _create_ratings_table(self, data: List[List], title: str) -> Table:
        """Create a ratings table."""
        table_data = data
        table = Table(table_data, colWidths=[1.5*inch, 0.8*inch])
        
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        table.setStyle(TableStyle(style))
        return table
    
    def _create_special_achievements_section(self, data: Dict[str, Any], division: str) -> List:
        """Create special achievements section."""
        content = []
        
        # Special Quality Point Register box
        special_data = [
            ["180 - Steve B, Scott W, David S(2), Eric H(2), KC, Stefano"],
            ["122 Out - Matt D"],
            ["6B - Eric H"],
            ["9H - Mike T(3), Megan(2), Ryan Mc, Mike R, Aaron"],
            ["9H - Matt M"]
        ]
        
        special_table = Table(special_data, colWidths=[4*inch])
        special_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ]))
        
        # Center the special achievements
        centered_table = Table([[special_table]], colWidths=[7*inch])
        centered_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        content.append(centered_table)
        content.append(Spacer(1, 15))
        
        return content
    
    def _create_league_summary(self, data: Dict[str, Any]) -> List:
        """Create charts for the report."""
        content = []
        content.append(PageBreak())
        content.append(Paragraph("Visual Statistics", self.styles['SectionHeader']))
        
        # Note: This is a placeholder for chart generation
        # In a full implementation, you would create actual charts using reportlab.graphics
        content.append(Paragraph(
            "Charts would be generated here showing player performance trends, "
            "score distributions, and other visual statistics.",
            self.styles['Normal']
        ))
        
        return content
