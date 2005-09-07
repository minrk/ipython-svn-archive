<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: verbatim.mod.xsl,v 1.16 2004/01/31 11:53:14 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template name="verbatim.apply.templates">
		<xsl:if test="ancestor::varlistentry">
			<!-- start the environment on a new line -->
			<xsl:text>\null{}</xsl:text>
		</xsl:if>
		<xsl:choose>
			<xsl:when test="ancestor::entry">
				<xsl:message>Problem with <xsl:value-of select="local-name(.)"/> inside table entries.</xsl:message>
				<xsl:text>\texttt{</xsl:text>
				<xsl:apply-templates mode="latex.verbatim"/>
				<xsl:text>}</xsl:text>
			</xsl:when>
			<xsl:when test="$latex.use.fancyvrb='1'">
				<xsl:variable name="not_monospaced" select="local-name(.)='literallayout' and @format!='monospaced'"/>
				<xsl:text>
\begin{Verbatim}[</xsl:text>
				<xsl:if test="@linenumbering='numbered'">
					<xsl:text>,numbers=left</xsl:text>
				</xsl:if>
				<xsl:if test="$not_monospaced">
					<xsl:text>,fontfamily=default</xsl:text>
				</xsl:if>
				<xsl:call-template name="latex.fancyvrb.options"/>
				<xsl:text>]
</xsl:text>
				<xsl:choose>
					<xsl:when test="$not_monospaced">
						<!-- Needs to be changed to cope with regular characterset! -->
						<xsl:apply-templates mode="latex.verbatim"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates mode="latex.verbatim"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>
\end{Verbatim}
</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>
\begin{verbatim}
</xsl:text>
				<xsl:apply-templates mode="latex.verbatim"/>
				<xsl:text>
\end{verbatim}
</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="address|screen|programlisting|literallayout">
		<xsl:call-template name="verbatim.apply.templates"/>
	</xsl:template><xsl:template name="next.is.verbatim">
		<xsl:param name="object" select="following-sibling::*[1]"/>
		<xsl:value-of select="count($object[self::address or self::screen or self::programlisting or self::literallayout])"/>
	</xsl:template><xsl:template match="literal" mode="latex.verbatim">
		<xsl:text>{\verb </xsl:text>
		<xsl:apply-templates mode="latex.verbatim"/>
		<xsl:text>}</xsl:text>
	</xsl:template></xsl:stylesheet>
