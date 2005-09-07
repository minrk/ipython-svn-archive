<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: mathelem.mod.xsl,v 1.4 2004/01/02 05:03:28 j-devenish Exp $		
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="mathelement">
		<xsl:apply-templates/>
	</xsl:template><xsl:template name="mathelement.environment">
		<xsl:param name="environment" select="'hypothesis'"/>
		<xsl:text>\begin{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}[{</xsl:text>
		<xsl:call-template name="normalize-scape">
			<xsl:with-param name="string" select="title"/> 
		</xsl:call-template>
		<xsl:text>}]
</xsl:text>
		<xsl:variable name="id"> <xsl:call-template name="label.id"/> </xsl:variable>
		<xsl:call-template name="content-templates"/>
		<xsl:text>\end{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}
</xsl:text>
	</xsl:template><xsl:template match="mathelement/mathhypothesis">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'hypothesis'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/mathremark">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'rem'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/mathexample">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'exm'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/mathproposition">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'prop'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/maththeorem">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'thm'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/mathdefinition">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'defn'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/mathlemma">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'lem'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathelement/mathproof">
		<xsl:call-template name="mathelement.environment">
			<xsl:with-param name="environment" select="'proof'"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="mathphrase|mathcondition|mathassertion">
		<xsl:apply-templates/>
	</xsl:template></xsl:stylesheet>
