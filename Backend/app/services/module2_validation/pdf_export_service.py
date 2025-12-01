"""
PDF Export Service
Generates PDF reports for validation results
"""

from typing import Dict, Any, Optional
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.spider import SpiderChart
from app.core.logging import logger


class PDFExportService:
    """Service for generating PDF validation reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a4a4a'),
            spaceAfter=20,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        ))
        
        # Score style (large, centered)
        self.styles.add(ParagraphStyle(
            name='ScoreStyle',
            parent=self.styles['Normal'],
            fontSize=36,
            textColor=colors.HexColor('#2c5aa0'),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        # Metric name style
        self.styles.add(ParagraphStyle(
            name='MetricName',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#1a1a1a'),
            fontName='Helvetica-Bold',
            spaceAfter=6
        ))
        
        # Body text style (use custom name to avoid conflict)
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a4a4a'),
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        # Recommendation style
        self.styles.add(ParagraphStyle(
            name='Recommendation',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c5aa0'),
            leftIndent=20,
            spaceAfter=6
        ))
    
    def generate_validation_pdf(
        self,
        export_data: Dict[str, Any]
    ) -> bytes:
        """
        Generate PDF report from validation export data
        
        Subtask 16.3
        Requirements: 15.1, 15.3
        
        Args:
            export_data: Complete validation export data (from export_validation_json)
            
        Returns:
            PDF file as bytes
        """
        try:
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build document content
            story = []
            
            # Add title page
            self._add_title_page(story, export_data)
            
            # Add executive summary
            self._add_executive_summary(story, export_data)
            
            # Add overall score section
            self._add_overall_score_section(story, export_data)
            
            # Add visualizations
            self._add_visualizations(story, export_data)
            
            # Add detailed scores
            self._add_detailed_scores(story, export_data)
            
            # Add strengths and weaknesses
            self._add_strengths_weaknesses(story, export_data)
            
            # Add recommendations
            self._add_recommendations(story, export_data)
            
            # Add idea details
            self._add_idea_details(story, export_data)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF report for validation {export_data.get('validation_id')}")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            raise
    
    def _add_title_page(self, story: list, export_data: Dict[str, Any]):
        """Add title page to PDF"""
        idea = export_data.get("idea", {})
        validation = export_data.get("validation", {})
        
        # Title
        title = Paragraph(
            f"Idea Validation Report",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        # Idea title
        idea_title = Paragraph(
            f"<b>{idea.get('title', 'Untitled Idea')}</b>",
            self.styles['CustomSubtitle']
        )
        story.append(idea_title)
        story.append(Spacer(1, 0.5 * inch))
        
        # Validation info table
        validation_info = [
            ['Validation ID:', validation.get('validation_id', 'N/A')],
            ['Validation Date:', self._format_date(validation.get('created_at'))],
            ['Status:', validation.get('status', 'N/A').upper()],
            ['Overall Score:', f"{export_data.get('validation', {}).get('overall_score', 0):.2f} / 5.0"]
        ]
        
        info_table = Table(validation_info, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a4a4a')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(info_table)
        story.append(PageBreak())
    
    def _add_executive_summary(self, story: list, export_data: Dict[str, Any]):
        """Add executive summary section"""
        report = export_data.get("report", {})
        executive_summary = report.get("executive_summary")
        
        if executive_summary:
            story.append(Paragraph("Executive Summary", self.styles['CustomSubtitle']))
            story.append(Spacer(1, 0.1 * inch))
            
            summary_text = Paragraph(executive_summary, self.styles['CustomBodyText'])
            story.append(summary_text)
            story.append(Spacer(1, 0.3 * inch))
    
    def _add_overall_score_section(self, story: list, export_data: Dict[str, Any]):
        """Add overall score section with visual indicator"""
        validation = export_data.get("validation", {})
        overall_score = validation.get("overall_score", 0)
        
        story.append(Paragraph("Overall Validation Score", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Large score display
        score_color = self._get_score_color(overall_score)
        score_text = f'<font color="{score_color}">{overall_score:.2f} / 5.0</font>'
        score_para = Paragraph(score_text, self.styles['ScoreStyle'])
        story.append(score_para)
        
        # Score interpretation
        interpretation = self._get_score_interpretation(overall_score)
        interp_para = Paragraph(
            f"<i>{interpretation}</i>",
            self.styles['CustomBodyText']
        )
        story.append(interp_para)
        story.append(Spacer(1, 0.3 * inch))
    
    def _add_visualizations(self, story: list, export_data: Dict[str, Any]):
        """Add visualization charts"""
        scores = export_data.get("scores", {})
        
        if not scores:
            return
        
        story.append(Paragraph("Score Visualization", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Create bar chart (radar chart is complex, skip for now)
        bar_chart = self._create_bar_chart(scores)
        if bar_chart:
            story.append(bar_chart)
            story.append(Spacer(1, 0.3 * inch))
    
    def _create_radar_chart(self, scores: Dict[str, Any]) -> Optional[Drawing]:
        """Create radar/spider chart for scores"""
        try:
            drawing = Drawing(400, 300)
            
            # Prepare data
            labels = []
            values = []
            
            metric_display_names = {
                "problem_clarity": "Problem Clarity",
                "market_demand": "Market Demand",
                "solution_fit": "Solution Fit",
                "differentiation": "Differentiation",
                "technical_feasibility": "Tech Feasibility",
                "market_size": "Market Size",
                "monetization_potential": "Monetization",
                "risk_level": "Risk Level",
                "user_validation_evidence": "User Validation"
            }
            
            for metric, score_data in scores.items():
                if isinstance(score_data, dict) and 'value' in score_data:
                    labels.append(metric_display_names.get(metric, metric))
                    values.append(score_data['value'])
            
            if not values:
                return None
            
            # Create spider chart
            spider = SpiderChart()
            spider.x = 50
            spider.y = 50
            spider.width = 300
            spider.height = 200
            spider.data = [values]
            spider.labels = labels
            
            # Configure strands (number of axes)
            num_strands = len(labels)
            spider.strands = num_strands
            
            # Configure strand properties (must be a list)
            from reportlab.graphics.charts.spider import StrandProperty
            spider.strands = [StrandProperty() for _ in range(num_strands)]
            for strand in spider.strands:
                strand.fillColor = colors.HexColor('#2c5aa0')
                strand.strokeColor = colors.HexColor('#1a1a1a')
                strand.strokeWidth = 1
            
            drawing.add(spider)
            
            return drawing
            
        except Exception as e:
            logger.warning(f"Failed to create radar chart: {str(e)}")
            return None
    
    def _create_bar_chart(self, scores: Dict[str, Any]) -> Optional[Drawing]:
        """Create bar chart for scores"""
        try:
            drawing = Drawing(500, 250)
            
            # Prepare data
            labels = []
            values = []
            
            metric_display_names = {
                "problem_clarity": "Problem\nClarity",
                "market_demand": "Market\nDemand",
                "solution_fit": "Solution\nFit",
                "differentiation": "Differenti-\nation",
                "technical_feasibility": "Tech\nFeasibility",
                "market_size": "Market\nSize",
                "monetization_potential": "Monetiz-\nation",
                "risk_level": "Risk\nLevel",
                "user_validation_evidence": "User\nValidation"
            }
            
            for metric, score_data in scores.items():
                if isinstance(score_data, dict) and 'value' in score_data:
                    labels.append(metric_display_names.get(metric, metric))
                    values.append(score_data['value'])
            
            if not values:
                return None
            
            # Create bar chart
            bar_chart = VerticalBarChart()
            bar_chart.x = 50
            bar_chart.y = 50
            bar_chart.width = 400
            bar_chart.height = 150
            bar_chart.data = [values]
            bar_chart.categoryAxis.categoryNames = labels
            bar_chart.valueAxis.valueMin = 0
            bar_chart.valueAxis.valueMax = 5
            bar_chart.valueAxis.valueStep = 1
            
            # Styling
            bar_chart.bars[0].fillColor = colors.HexColor('#2c5aa0')
            bar_chart.bars[0].strokeColor = colors.HexColor('#1a1a1a')
            bar_chart.bars[0].strokeWidth = 1
            
            # Category axis styling
            bar_chart.categoryAxis.labels.fontSize = 7
            bar_chart.categoryAxis.labels.angle = 0
            
            # Value axis styling
            bar_chart.valueAxis.labels.fontSize = 8
            
            drawing.add(bar_chart)
            
            return drawing
            
        except Exception as e:
            logger.warning(f"Failed to create bar chart: {str(e)}")
            return None
    
    def _add_detailed_scores(self, story: list, export_data: Dict[str, Any]):
        """Add detailed scores section"""
        scores = export_data.get("scores", {})
        
        if not scores:
            return
        
        story.append(PageBreak())
        story.append(Paragraph("Detailed Metric Scores", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        metric_display_names = {
            "problem_clarity": "Problem Clarity",
            "market_demand": "Market Demand",
            "solution_fit": "Solution Fit",
            "differentiation": "Differentiation",
            "technical_feasibility": "Technical Feasibility",
            "market_size": "Market Size",
            "monetization_potential": "Monetization Potential",
            "risk_level": "Risk Assessment",
            "user_validation_evidence": "User Validation Evidence"
        }
        
        for metric, score_data in scores.items():
            if not isinstance(score_data, dict):
                continue
            
            # Metric section
            metric_elements = []
            
            # Metric name and score
            metric_name = metric_display_names.get(metric, metric.replace('_', ' ').title())
            score_value = score_data.get('value', 0)
            score_color = self._get_score_color(score_value)
            
            metric_header = Paragraph(
                f'<b>{metric_name}</b>: <font color="{score_color}">{score_value}/5</font>',
                self.styles['SectionHeading']
            )
            metric_elements.append(metric_header)
            
            # Justifications
            justifications = score_data.get('justifications', [])
            if justifications:
                metric_elements.append(Paragraph("<b>Justifications:</b>", self.styles['MetricName']))
                for justification in justifications:
                    bullet = Paragraph(f"• {justification}", self.styles['CustomBodyText'])
                    metric_elements.append(bullet)
                metric_elements.append(Spacer(1, 0.1 * inch))
            
            # Recommendations
            recommendations = score_data.get('recommendations', [])
            if recommendations:
                metric_elements.append(Paragraph("<b>Recommendations:</b>", self.styles['MetricName']))
                for recommendation in recommendations[:3]:  # Limit to top 3
                    bullet = Paragraph(f"• {recommendation}", self.styles['Recommendation'])
                    metric_elements.append(bullet)
            
            metric_elements.append(Spacer(1, 0.2 * inch))
            
            # Keep metric section together
            story.append(KeepTogether(metric_elements))
    
    def _add_strengths_weaknesses(self, story: list, export_data: Dict[str, Any]):
        """Add strengths and weaknesses section"""
        report = export_data.get("report", {})
        strengths = report.get("strengths", [])
        weaknesses = report.get("weaknesses", [])
        
        if not strengths and not weaknesses:
            return
        
        story.append(PageBreak())
        story.append(Paragraph("Key Insights", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Strengths
        if strengths:
            story.append(Paragraph("Strengths", self.styles['SectionHeading']))
            for strength in strengths:
                bullet = Paragraph(
                    f'• <font color="#2c5aa0">{strength.replace("_", " ").title()}</font>',
                    self.styles['CustomBodyText']
                )
                story.append(bullet)
            story.append(Spacer(1, 0.2 * inch))
        
        # Weaknesses
        if weaknesses:
            story.append(Paragraph("Areas for Improvement", self.styles['SectionHeading']))
            for weakness in weaknesses:
                bullet = Paragraph(
                    f'• <font color="#d32f2f">{weakness.replace("_", " ").title()}</font>',
                    self.styles['CustomBodyText']
                )
                story.append(bullet)
            story.append(Spacer(1, 0.2 * inch))
    
    def _add_recommendations(self, story: list, export_data: Dict[str, Any]):
        """Add critical recommendations section"""
        report = export_data.get("report", {})
        recommendations = report.get("critical_recommendations", [])
        
        if not recommendations:
            return
        
        story.append(Paragraph("Critical Recommendations", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.1 * inch))
        
        for i, recommendation in enumerate(recommendations[:5], 1):  # Top 5
            rec_para = Paragraph(
                f"<b>{i}.</b> {recommendation}",
                self.styles['CustomBodyText']
            )
            story.append(rec_para)
            story.append(Spacer(1, 0.1 * inch))
        
        story.append(Spacer(1, 0.2 * inch))
    
    def _add_idea_details(self, story: list, export_data: Dict[str, Any]):
        """Add idea details appendix"""
        idea = export_data.get("idea", {})
        
        story.append(PageBreak())
        story.append(Paragraph("Idea Details", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Problem statement
        if idea.get('problem_statement'):
            story.append(Paragraph("<b>Problem Statement:</b>", self.styles['MetricName']))
            story.append(Paragraph(idea['problem_statement'], self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.15 * inch))
        
        # Solution description
        if idea.get('solution_description'):
            story.append(Paragraph("<b>Solution Description:</b>", self.styles['MetricName']))
            story.append(Paragraph(idea['solution_description'], self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.15 * inch))
        
        # Target market
        if idea.get('target_market'):
            story.append(Paragraph("<b>Target Market:</b>", self.styles['MetricName']))
            story.append(Paragraph(idea['target_market'], self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.15 * inch))
        
        # Business model
        if idea.get('business_model'):
            story.append(Paragraph("<b>Business Model:</b>", self.styles['MetricName']))
            story.append(Paragraph(idea['business_model'], self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.15 * inch))
        
        # Team capabilities
        if idea.get('team_capabilities'):
            story.append(Paragraph("<b>Team Capabilities:</b>", self.styles['MetricName']))
            story.append(Paragraph(idea['team_capabilities'], self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.15 * inch))
        
        # Linked pain points
        linked_pain_points = idea.get('linked_pain_points', [])
        if linked_pain_points:
            story.append(Paragraph("<b>Linked Pain Points:</b>", self.styles['MetricName']))
            story.append(Paragraph(
                f"{len(linked_pain_points)} pain point(s) from Problem Discovery module",
                self.styles['CustomBodyText']
            ))
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score value"""
        if score >= 4.0:
            return "#2e7d32"  # Green
        elif score >= 3.0:
            return "#f57c00"  # Orange
        else:
            return "#d32f2f"  # Red
    
    def _get_score_interpretation(self, score: float) -> str:
        """Get interpretation text for overall score"""
        if score >= 4.5:
            return "Excellent - Strong validation across all metrics"
        elif score >= 4.0:
            return "Very Good - Solid validation with minor areas for improvement"
        elif score >= 3.5:
            return "Good - Promising idea with some areas needing attention"
        elif score >= 3.0:
            return "Fair - Moderate validation, significant improvements recommended"
        elif score >= 2.0:
            return "Weak - Major concerns identified, substantial work needed"
        else:
            return "Poor - Critical issues across multiple dimensions"
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """Format ISO date string to readable format"""
        if not date_str:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p UTC")
        except:
            return date_str
