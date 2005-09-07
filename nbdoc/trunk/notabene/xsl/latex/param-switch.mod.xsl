<?xml version="1.0"?>
<!--############################################################################
|	$Id: param-switch.mod.xsl,v 1.19 2004/08/12 12:04:36 j-devenish Exp $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:param name="latex.caption.lot.titles.only">1</xsl:param><xsl:param name="latex.bibfiles"/><xsl:param name="latex.math.support">1</xsl:param><xsl:param name="latex.output.revhistory">1</xsl:param><xsl:template name="latex.fancybox.options">
	</xsl:template><xsl:param name="latex.pdf.support">1</xsl:param><xsl:param name="latex.generate.indexterm">1</xsl:param><xsl:param name="latex.hyphenation.tttricks">0</xsl:param><xsl:param name="latex.decimal.point"/><xsl:param name="latex.trim.verbatim">0</xsl:param><xsl:param name="latex.use.ltxtable">0</xsl:param><xsl:param name="latex.use.longtable">0</xsl:param><xsl:param name="latex.use.overpic">1</xsl:param><xsl:param name="latex.use.umoline">0</xsl:param><xsl:param name="latex.use.url">1</xsl:param><xsl:param name="latex.is.draft"/><xsl:param name="latex.use.varioref">
		<xsl:if test="$insert.xref.page.number='1'">1</xsl:if>
	</xsl:param><xsl:param name="latex.use.fancyhdr">1</xsl:param><xsl:param name="latex.bridgehead.in.lot">1</xsl:param><xsl:param name="latex.fancyhdr.truncation.style">io</xsl:param><xsl:param name="latex.fancyhdr.truncation.partition">50</xsl:param><xsl:param name="latex.fancyhdr.style"/><xsl:param name="latex.use.parskip">0</xsl:param><xsl:param name="latex.use.noindent">
		<xsl:choose>
			<xsl:when test="$latex.use.parskip=1">
				<xsl:value-of select="0"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="1"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:param><xsl:param name="latex.use.subfigure">1</xsl:param><xsl:param name="latex.use.rotating">1</xsl:param><xsl:param name="latex.use.tabularx">1</xsl:param><xsl:param name="latex.use.dcolumn">0</xsl:param><xsl:param name="latex.use.hyperref">1</xsl:param><xsl:param name="latex.use.fancybox">1</xsl:param><xsl:param name="latex.use.fancyvrb">1</xsl:param><xsl:param name="latex.use.isolatin1">0</xsl:param><xsl:param name="latex.use.ucs">0</xsl:param><xsl:param name="latex.biblio.output">all</xsl:param><xsl:param name="latex.biblioentry.style"/><xsl:param name="latex.caption.swapskip">1</xsl:param><xsl:param name="latex.graphics.formats"/><xsl:param name="latex.entities"/><xsl:param name="latex.otherterm.is.preferred">1</xsl:param><xsl:param name="latex.alt.is.preferred">1</xsl:param><xsl:param name="latex.apply.title.templates">1</xsl:param><xsl:param name="latex.apply.title.templates.admonitions">1</xsl:param><xsl:param name="latex.url.quotation">1</xsl:param><xsl:param name="latex.ulink.protocols.relaxed">
      <xsl:choose>
         <xsl:when test="$ulink.protocols.relaxed!=''">
            <xsl:message>Warning: $ulink.protocols.relaxed was a misnomer: use $latex.ulink.protocols.relaxed instead</xsl:message>
            <xsl:value-of select="$ulink.protocols.relaxed"/>
         </xsl:when>
			<xsl:otherwise>
            <xsl:value-of select="1"/>
			</xsl:otherwise>
      </xsl:choose>
   </xsl:param><xsl:param name="ulink.protocols.relaxed"/><xsl:param name="latex.suppress.blank.page.headers">1</xsl:param></xsl:stylesheet>
