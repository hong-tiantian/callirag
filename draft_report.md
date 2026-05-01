# Topic: Chinese Calligraphy Generation via RAG

## Introduction

From the digitisation of endangered scripts to the refinement of historical texts, Chinese calligraphy generation has cultural and educational value that supports multiple downstream tasks [@2025wangdeep; @2025zhoucalliformer; @2026xuunicalli].

Chinese calligraphy generation, as a branch of font generation, is normally regarded as an image-to-image translation task, in which the models preserve the content of the source domain and transfer the style of the target domain to generate target glyphs [@2025wangdeep].

However, it poses greater challenges in that it is not merely image synthesis, but a constrained visual-symbol generation task. Chinese calligraphy generation in the context of deep learning is a highly constrained task [@2025wangdeep]:

1) \textbf{Content correctness}: Covering Chinese characters is a long-tailed problem. Covering rare and complex characters is not readily achieved by models. There are 6,763 commonly used characters under the Chinese GB2312 standard, a number that rises to around 10,000 when traditional characters are included [@2025wangdeep; @2026rensurvey]. Rare and complex characters appear very infrequently in training data. Reliance on purely parametric memorization is often not sufficient [@2024hedifffontb; @2025chenadvancements]. This issue is not only about coverage, but also directly affects structural correctness, as rare and complex characters are more prone to structural errors.

2) \textbf{Structural integrity}: Chinese characters are composed of various components and strokes, which together determine whether a glyph is well-formed [@2025liucr; @2017zhangonline]. The location, proportion, and variation of the same radical differ in different characters. So, beyond the correctness of the characters, if models do not understand the spatial constraint relations between component layout, glyph collapse is likely. 

3) \textbf{Stylistic expressiveness}: Chinese calligraphy is not merely a variation of standard fonts but a form shaped by dynamic stroke trajectories, variations in pressure, and structural transformation in the act of writing [@2017chencalligraphy; @2022qiucalligraphy; @2025wangdeep]. This makes the problem more difficult than ordinary font transfer. Different scripts differ from one another, and within a single script, the same stroke can vary across characters.

These constraints are not independent. In calligraphy, style is often realized through structural deformation, stroke connection, and writing rhythm rather than surface appearance alone. Different scripts, and even different hands within the same script, may compress, stretch, merge, or reconnect strokes in different ways. This means that stylistic variation does not simply add visual diversity; it can also enlarge the effective long tail of structurally difficult cases and makes the balance between structural correctness and stylistic expressiveness harder to maintain. Overall, the central challenge is to generate stylistic flexibility without violating task-critical structure.

Existing methods mainly tackle these constraints by scaling data and model capacity or by designing few-shot and condition-guided generation frameworks [@2025wangdeep; @2025chenadvancements; @2026rensurvey]. In essence, these approaches attempt to encode more knowledge into model parameters, so that the model can better memorize structural patterns and stylistic variation. However, this strategy is costly, because both calligraphy data and model training are expensive. To reduce this burden, some few-shot methods introduce reference-based or memory-augmented mechanisms [@2020chadualmemory; @2024parkfewshot; @2022tangfewshot]. Instead of relying only on parametric memorization, they provide external support at inference time, often without retraining, and thereby improve generalization to new styles or unseen combinations. Reference-based methods show that external examples matter, while memory-based methods show that reusable externalized knowledge matters. Yet in both cases, the support is usually limited to fixed reference inputs or model-internal memory, rather than explicit retrieval from a larger external pool for structurally relevant exemplars.

Following the long-tailed distribution, model parameters could not memorise all visual concepts. Therefore, what is missing is not reference in a vague sense, but a mechanism to obtain structurally relevant knowledge on demand at inference time, such as component layout relations, stroke connectivity, and script-specific structural variants for rare or complex characters. This limitation is even more serious in calligraphy, because script variation further enlarges the long tail and makes structural failure more likely. This is why retrieval becomes relevant for the task [@2025zhengragvision].

On a positive note, previous works have shown that Retrieval-Augmented Generation (RAG) can be effective for related long-tail generation tasks. RAG is a general paradigm that retrieves relevant information from an external knowledge base to guide generation [@2023gaoragsurvey; @2025zhengragvision]. This is especially important for tasks requiring high fidelity, strong structural constraints, and style consistency, where purely parametric memory is often insufficient. In fact, earlier reference-based and memory-augmented methods have already shown that non-parametric support can help generation become more stable and generalizable, and earlier retrieval-based image synthesis has also shown that retrieved visual patches can support generation through differentiable retrieval [@2020tsengretrievegan]. In this sense, the effectiveness of RAG is not isolated, but consistent with a broader line of evidence: when a task cannot be fully supported by model parameters alone, introducing external support can improve generation quality. This is also supported by recent visual RAG studies, where retrieval has been shown to help long-tailed visual generation, especially for rare entities and insufficiently covered visual concepts [@2025zhengragvision].

Given these advances, it is reasonable to introduce a RAG mechanism into Chinese calligraphy generation to fill the structural knowledge gap of parametric models. However, existing visual RAG methods operate at coarse granularities, such as prompt, entity, or layout level, whereas calligraphy ultimately requires support at the level of component layout, stroke connectivity, and script-specific structural variants. This retrieval should not be confused with the early component decomposition-and-assembly paradigm [@2005xuautomatic; @2009xuautomatic], where characters are split into parts and mechanically reassembled. Here, retrieval provides structural references to the generation model, while generation itself is still performed by the model. As a first step, this work investigates whether structure-aware whole-glyph retrieval can already improve generation quality for rare and complex characters. Finer-grained retrieval at the component or radical level is a natural extension, but validating the retrieval-augmented paradigm itself is a prerequisite.

The central research question is:
- Can structure-aware retrieval from an external knowledge base improve structural correctness for rare and complex Chinese characters in calligraphy generation?
- Does structurally filtered retrieval provide more benefit than unfiltered (random) retrieval, and how does the retrieval unit (whole-glyph vs. component-level) affect generation quality?
- Under what conditions does retrieval help most, for example in rare characters, complex layouts, or unseen characters?

The following review is therefore organized in three parts. It first examines structural modeling in calligraphy and font generation, then discusses style–structure interaction in calligraphy, and finally reviews external reference mechanisms from reference and memory to retrieval.


## Literature Review

### Structural modelling in calligraphy and font generation

#### Component and radical-based methods

By harnessing the obvious hierarchical structure of Chinese characters, many researchers have achieved better structure correctness and generation quality. This line of work can be traced back to the pre-deep-learning stage, when calligraphy generation was already explicitly modeled through radicals, strokes, and topological structure [@2005xuautomatic; @2009xuautomatic]. Since then, it has developed into the structure-aware deep generative paradigms we see today. In recent methods, structural modeling is no longer only handcrafted, but learned through GANs, Transformers, and Diffusion Models with component-level supervision, dynamic structural attention, or structure-aware guidance [@2022konglook; @2025liuchinese; @2025zhoucalliformer].

Chinese characters have three hierarchical levels, namely strokes, components or radicals, and whole glyphs, as well as a limited number of common spatial configurations such as left-right, top-bottom, and enclosure layouts [@2025wangdeep; @2025chenadvancements]. This compositional property is also well established in the character recognition literature, where characters are routinely decomposed into radicals or strokes for more effective processing [@2025liucr; @2017zhangonline]. Because of these properties, many approaches do not treat Chinese characters as ordinary pixel patterns, but as decomposable compositional objects. This is helpful for generalization, few-shot learning, and the preservation of local structural details such as stroke endings or turning points. These methods mainly differ in how such structural knowledge is represented.

One common line is to represent structure explicitly. In this setting, Chinese characters are decomposed into linear sequences of radicals or components [@2025liuchinese; @2020wucalligan]. The decomposed units are then transferred into dense vectors by an embedding layer. In CalliGAN, the component sequence is used to model dependency relations and writing order through an LSTM-based encoder [@2020wucalligan]. Liu et al. also condition a latent diffusion model on component sequences, while introducing a printed-font image as additional structural guidance, so that structural integrity can be better preserved during generation [@2025liuchinese].

Another line models structure more implicitly in feature space. Instead of directly feeding readable component sequences into the model, structural information is decomposed into factors, localized representations, or discrete codebooks, and then recomposed into a unified representation for generation [@2024parkfewshot; @2023panvqfont]. In calligraphy generation, this idea further develops into structure-aware feature fusion and alignment. For example, CalliFormer replaces earlier sequence-style component encoding with a structure-aware Transformer, so that spatial relations between components can be modeled more effectively [@2025zhoucalliformer]. Liu et al. combine local component conditions, global style conditions, and latent representation alignment to better coordinate structure and style [@2025liuchinese]. Similar ideas also appear in component-level supervision, where the generator is not only asked to produce a plausible whole glyph, but is also guided to respect finer sub-character structure [@2022konglook].

These technical paths can be effective, but they do not fully solve the problem. When structural guidance is too strong, stroke rendering may become less flexible, especially in running or cursive styles. At the same time, when characters contain many strokes or highly dense layouts, models may still produce collapsed glyphs, missing strokes, or local distortions [@2024hedifffontb; @2024lichinese].

More importantly, most of these methods still rely on structural priors learned at training time. Condition images such as SimSun printed fonts provide canonical structural guidance, but they are style-agnostic and static [@2025liuchinese]. They show what a character looks like in a standard form, not how it should be realised in a target calligraphic style. The model must still rely on parametric memory to bridge this gap, and that memory is often insufficient for characters poorly covered in training. Semantic embeddings face a similar limit: they encode category meaning more readily than spatial configuration. As a result, existing models generally lack a mechanism to acquire new structural knowledge at inference time. This limitation is most visible in rare and complex characters, where single-character generation remains vulnerable to structural errors [@2024hedifffontb].

#### Skeleton and contour-based methods

Another line of work models structure not through components or radicals, but through writing trajectories, skeleton-like geometry, or contour-level guidance. This direction is motivated by the fact that Chinese characters, especially in calligraphy, are not only compositional, but also geometric and procedural. Their structure can be reflected in stroke paths, topological relations, and the writing process itself [@2025chenadvancements; @2017zhangonline].

Some methods focus on writing trajectories. Instead of representing a character only as a final raster image, they encode it as a sequence of coordinates or control labels, so that the writing action can be described more precisely. This is particularly relevant for calligraphy, where stroke continuity and ligature matter. DeepCalliFont is a representative example. It integrates image synthesis and sequence generation in a dual-modality framework, so that glyph images and writing sequences can support each other during generation [@2024liudeepcallifont].

Although they belong to the diffusion-based line, some methods also show that finer structural conditions at the stroke level matter for preserving complex character structure. DP-Font introduces stroke-order constraints and combines them with physical information neural networks, so that the generated calligraphy not only follows structural logic but also reflects more realistic writing dynamics [@2024zhangdpfont]. Diff-Font and MS-Font use stroke count or other stroke- or component-level fine-grained conditions to stabilize one-shot generation and improve the preservation of intricate character structures [@2024hedifffontb; @2024lichinese]. These methods are not pure skeleton models in a strict sense, but they still support the broader point that more fine-grained structural cues are important for difficult Chinese characters.

To recover more detailed appearance, some studies further move from trajectory or skeleton to contour-level modeling. In this sense, the process goes from the inside out: skeleton or trajectory first provides a relatively stable content structure, and contour-level rendering then turns that abstract path into a specific calligraphic glyph. SCFont is a typical example. It uses a two-stage process, where writing trajectories are synthesized first and contour details are then recovered on top of them [@2019jiangscfont]. CRA-GAN also shows that contour and region-aware guidance can provide delicate structural and stylistic cues, helping the model better capture complex calligraphic morphology [@2023zengenhancing].

This line of work is important because it shows that structure can guide style progressively. Trajectory or skeleton gives a relatively stable inner scaffold, while contour information helps recover visible details such as stroke thickness, turning shapes, and outer boundaries. In other words, contour is not merely decorative. It can also serve as a strong auxiliary signal for preserving the visual integrity of calligraphic forms.

However, these methods still have limitations. Some rely on fixed guidance, handcrafted procedures, or reference forms that are costly to adapt across large character sets. Others remain inflexible when the target handwriting departs from the reference form. More importantly, their structural priors are still learned or fixed in advance, rather than acquired on demand at inference time. When models face rare characters, dense layouts, or script-specific structural variants, the support they can provide is still limited.

Both component-based and skeleton/contour-based methods suggest that structural modelling can improve generation quality. Yet in all cases, structural priors are derived from training data. Before examining how external mechanisms might address this limitation, it is necessary to consider how style interacts with structure in calligraphy. In different scripts, the same character undergoes different structural deformations: stroke connectivity changes, radical boundaries blur, and component layouts shift. Style variation is therefore not independent of structure; it reshapes structure itself. This interaction determines what kind of structural knowledge is needed and why training data alone is unlikely to cover the full combinatorial space.


### Style modelling and structural interaction

#### Style representation and transfer

Style representation and transfer mainly follow the content–style disentanglement paradigm [@2025chenadvancements; @2026rensurvey]. In these methods, a font is usually decomposed into the structural content of characters and the stylistic characteristics of the target font, and the decoder then injects style into structure during generation. In practice, this line is mainly implemented through two architectures: GAN-based methods, which typically use a content encoder, a style encoder, a mixer, and a decoder [@2018zhangseparating; @2021zhouendend; @2024daichinese], and diffusion-based methods, which introduce external conditions into the denoising process to control style generation [@2023liaocalliffusion; @2025liumoyun].

There are roughly three levels at which style is modeled. The first is global style representation, which captures relatively universal properties such as glyph size, stroke thickness, and spacing [@2018zhangseparating; @2021xiedgfont]. However, global vectors are often too coarse to describe local stroke morphology or serif-like details. The second is component-wise style modeling, where style is learned over smaller sub-character units rather than over the whole glyph. This improves fine-grained transfer, but usually depends on predefined components such as radicals or stroke labels, which is labor-intensive and weak in generalization for complex scripts [@2024parkfewshot; @2023panvqfont]. The third is fine-grained local style modeling. Instead of treating style as a single vector, these methods model local style at different spatial locations in the feature map, often through cross-attention between content and reference images [@2022tangfewshot]. Some newer methods also use vector quantization to learn discrete local codes automatically, without manually defining component labels [@2023panvqfont].

To improve style consistency, existing methods tackle the problem at several complementary levels. At the architectural level, some models try to separate structure and style through staged generation. MSD-Font, for example, splits the diffusion process into structure construction, font transfer, and font refinement stages, so that global structure is established before stylistic details are added [@2024fugenerate]. Other methods adopt more integrated generation frameworks [@2021zhouendend; @2024daichinese]. At the feature level, style can be aggregated globally through similarity-weighted mechanisms [@2023panvqfont] or modeled locally through learned geometric deformations. DG-Font, for instance, uses deformable convolutions to predict displacement maps between content and style features, so that style transfer is treated as spatial deformation rather than texture replacement [@2021xiedgfont]. At the optimisation level, FontDiffuser combines multi-scale content aggregation with style contrastive learning, so that both complex character structure and large style variation can be handled more robustly [@2024yangfontdiffuser]. LoRA-based few-shot adaptation [@2023liaocalliffusion] further strengthens transfer efficiency under limited references. In other words, recent work no longer treats style transfer as a simple one-step texture translation problem, but as a multi-level control problem over global impression, local variation, and transfer stability.

These methods do improve per-character style transfer, but style consistency across a whole character set is still difficult to maintain. Calligraphic style is not only about overall visual tone. It also includes stroke weight, pressure variation, ink spread, connective flow, and the repeated way in which the same structural unit is deformed across characters. A coherent style therefore requires the same radical or stroke pattern to preserve comparable rhythm and visual logic in different characters. Under single-reference conditions, which are common in rare calligraphic scripts, this becomes even harder [@2024hedifffontb]. Component-based methods may improve local precision, but they may still render the same radical inconsistently across characters, especially when reference selection is limited or unstable [@2025liuchinese; @2023panvqfont].

The limitation is not only architectural. Some methods assume that structure and style can be cleanly disentangled, while others discretize local style into fixed codebooks or depend heavily on complicated cross-attention and carefully chosen references. These choices can improve transfer performance, but they also introduce representational bottlenecks. Beyond these architectural choices, style consistency is also constrained by training coverage. No single training set is likely to fully span the combinatorial space of radicals, layouts, scripts, and individual hands. Scaling data or adapting style at test time may improve transfer, but it still does not provide new structural knowledge for unseen or weakly covered characters. For this reason, style modeling in Chinese calligraphy cannot be discussed independently from structure.

#### Structure and style entanglement in calligraphy

In calligraphy, style is not simply added on top of an already fixed structure. More often, style is realized through structural variation itself, and then further shaped by stroke thickness, brush-tip behavior, pressure change, and ink effects. In this sense, calligraphic style is not merely a surface property, but a structured way of deforming and re-realizing a character form [@2017chencalligraphy; @2021xiedgfont].

This becomes more obvious in running and cursive scripts. In these cases, stroke connection and stroke merging are common. Two strokes that are separate in a regular form may be linked into one continuous movement, and the result can be highly irregular and difficult to predict in cursive writing [@2024liaocalliffusionv2]. The component layout of the same character may also differ substantially from its standard form. Stroke connectivity changes, radical boundaries become less clear, and some local structures may be compressed, stretched, or rebalanced to preserve the overall rhythm of the hand. Style, in other words, does not merely decorate structure; it breaks, reorganizes, and redefines it within acceptable calligraphic constraints.

Artistic intention makes this even more complex. Calligraphers do not write each character as an isolated canonical unit. They adjust width, height, slant, density, and internal balance according to the overall visual flow and aesthetic effect of the work. As a result, even within a single style, the same character may undergo different structural distortions in different contexts. UniCalli further demonstrates this at the column level, where ligature continuity, inter-character spacing, and layout rhythm add structural constraints beyond single-character generation; its joint generation-recognition framework also shows that recognition can serve as an effective structural constraint for generation [@2026xuunicalli]. Structure and style cannot be cleanly separated in calligraphy as they sometimes can in ordinary font transfer. Once style is understood as structured deformation rather than appearance variation, style diversity is no longer an independent challenge. It becomes a condition that makes structural correctness even harder to preserve.

This also explains why training-time structural priors are often insufficient. The model does not only need to remember the canonical structure of each character. It must also cope with the structural variants of that character under different scripts and different hands. The space of possible combinations is much larger than ordinary glyph generation, and likely beyond what training data can fully cover. Therefore, the difficulty of calligraphy generation lies not only in transferring style, but in generating stylistic variation without violating task-critical structure.


### External reference mechanisms

#### Reference and memory-based generation

Since purely parametric learning is limited by training coverage, some existing methods have already introduced external reference or memory mechanisms. In other words, the idea of relying on information outside the main generator is not new in font and calligraphy generation. What changes is the granularity of that information, and when it is used.

In few-shot font generation, reference-based methods are almost a standard setting. The basic logic is simple. Instead of asking the model to memorise a whole font style in parameters, the model observes a few reference glyphs and extracts style cues from them. This is important for Chinese, because the number of characters is too large, and the cost of manual font design is too high [@2025wangdeep]. However, early reference use is often coarse. When reference images are encoded into a global style representation, the model can capture overall traits such as thickness, size, or rough visual tone, but much less local structural and stroke detail.

This is why later methods move from global reference to finer reference use. A representative direction is component-aware or localised reference modeling. DM-Font stores compositional knowledge through a dual memory design, where persistent memory keeps component-level structural embeddings and dynamic memory stores style-dependent component features extracted from the given references [@2020chadualmemory]. LF-Font also shows that localised representations are more suitable than a single global style vector for complex scripts such as Chinese, because style is distributed over components rather than concentrated in one holistic code [@2024parkfewshot]. Similarly, fine-grained local style transfer aligns content and reference at spatial locations, so that local style can be assigned to the right part of the target glyph [@2022tangfewshot]. VQ-Font goes one step further and learns component-level local codes automatically, without relying on manually predefined radicals or strokes [@2023panvqfont].

These methods are important because they show one consistent fact. If reference is too coarse, it is difficult to preserve detailed calligraphic traits. If reference is brought to the component or local level, generation tends to become more stable for complex glyphs and few-shot settings. So the value of reference is not just that it provides style examples. More importantly, it provides structured support. In Chinese character generation, this support is often inseparable from how components are arranged, matched, and rendered.

Memory-based methods follow a similar logic, but in a more explicit storage form. They do not only look at the current reference input, but also maintain reusable units of knowledge. This is useful because structure-related patterns can be stored and called when needed, while style-related signals can still adapt to the input examples [@2020chadualmemory]. In this sense, memory methods already imply a shift from pure generation to generation with external support.

However, these methods are still not retrieval in the strict RAG sense. Their external information is usually fixed in the model design, or limited to a small number of given references. The model does not actively search a larger external pool at inference time for structurally relevant exemplars. So although they reduce the burden on pure parametric memorisation, they still do not solve the more general problem. When facing rare characters, complex layouts, or script-specific structural variants not well covered in training, the model still lacks a mechanism to acquire the missing knowledge on demand.

#### RAG in image generation

In the broader image generation literature, retrieval augmentation has been shown to be effective for rare and long-tail content. Unlike conventional reference-based generation, RAG does not only condition on a fixed input example. It retrieves relevant external information at inference time, and uses that information to support generation [@2023gaoragsurvey].

This matters because long-tail problems are not unique to text generation. In visual generation, model parameters alone are unlikely to fully memorise all rare entities, layouts, or visual concepts. Retrieval therefore becomes a way to provide non-parametric support when the target content is uncommon or insufficiently represented in training data [@2025zhengragvision].

Existing visual RAG methods already show a gradual movement towards finer granularity. Re-Imagen retrieves image-text pairs for rare entities, so that generation can be guided by both semantic description and visual appearance [@2022chenreimagen]. RDM retrieves semantically related images and injects their representations into diffusion models, showing that external visual databases can improve generation quality without retraining the whole model [@2022blattmannretrievalaugmented]. FineRAG further decomposes complex prompts into smaller queries, retrieves references for each sub-part, and combines them through a more fine-grained pipeline [@2025yuanfinerag]. Retrieval-augmented layout generation also shows that external structurally similar exemplars can support composition and reduce dependence on large-scale training data [@2024horitaretrievalaugmented].

From another angle, some calligraphy or font related methods already touch part of this idea, although they are not yet full RAG frameworks. Calliffusion and Moyun use categorical labels of character, script, and style as control signals for calligraphy generation [@2023liaocalliffusion; @2025liumoyun]. This shows that generation can benefit from external information beyond a fixed image pair. But categorical labels are still coarser than the structural knowledge needed for difficult Chinese characters. They cannot tell the model how a rare glyph should organise components or maintain stroke connectivity under a specific script.

So the broader literature gives a positive signal. Retrieval can help long-tail generation. It can also work in visual domains, not only in language tasks. But the way existing RAG methods retrieve and inject knowledge is still largely designed for natural images, objects, scenes, and prompt entities. The unit they retrieve is usually a whole image, an image-text pair, an object concept, or a layout pattern. That is useful, but it is not yet the unit that Chinese calligraphy generation needs most.

#### Retrieval granularity mismatch

The gap, then, is not that calligraphy generation has no reference mechanism at all. The gap is that the granularity of existing external reference mechanisms does not match the granularity of structural knowledge required by calligraphy generation.

For Chinese calligraphy, what is often missing is much more specific. It may be component layout under a certain script, stroke connectivity in a running or cursive form, or a structurally similar exemplar for a rare character whose full form is not well learned by the model. A whole-character reference may help, but it is often too coarse. A global style vector is even coarser. Prompt-level or entity-level retrieval in visual RAG is also not enough, because a Chinese character is not a natural image entity. Its correctness depends on internal compositional relations.

This means that calligraphy generation raises a retrieval question with potentially multiple levels of granularity: whole-glyph exemplars that share the same spatial configuration, component-level cues such as shared radicals, or other script-appropriate substructures. In the long run, the model may benefit from retrieval at finer levels. However, before exploring component-level retrieval, a prior question must be answered: does structure-aware retrieval help calligraphy generation at all? If even whole-glyph retrieval guided by structural configuration does not improve generation quality, there is little reason to pursue finer granularities. At the same time, this retrieval should not be confused with the early split-and-assemble paradigm [@2005xuautomatic; @2009xuautomatic]. The point here is not to manually decompose a character and directly stitch parts together. The point is to provide structural references to the generator, while generation itself is still performed by the model.

Therefore, reference-based generation, memory-augmented generation, and visual RAG can be seen as three related but different stages. Reference-based methods show that external examples matter. Memory-based methods show that reusable externalised knowledge matters. RAG further suggests that such knowledge can be retrieved dynamically at inference time from a larger pool. What remains underexplored is how to make this retrieval match the internal structure of Chinese calligraphy generation.

This is exactly where the present work is positioned. It does not ask whether external information is useful in general, because previous work already suggests that it is. The more specific question is whether structure-aware retrieval from an external knowledge base can improve glyph integrity for rare and complex Chinese characters, where training-time structural priors are likely insufficient. As a first investigation, this work adopts whole-glyph retrieval guided by structural configuration type, and examines whether and when such retrieval improves generation quality. This serves as a foundation for future work on finer-grained retrieval strategies.


## Method

This section describes the proposed retrieval-augmented framework for Chinese calligraphy generation. The method is built on top of FontDiffuser [@2024yangfontdiffuser] as the base generator, and introduces an external retrieval mechanism to provide structural support at inference time for rare and complex characters.

This work focuses on **structural correctness** as the primary objective, under a controlled stylistic setting: all experiments use regular script (楷书) with a same-style knowledge base. Style diversity across scripts (e.g., running, cursive) is an important challenge but is deliberately excluded from the scope of this study, in order to isolate the effect of retrieval on structural quality.

### Problem Setting

The task is single-character Chinese calligraphy generation in a few-shot setting. Given a small set of reference glyphs in a target calligraphic style and a content specification (character identity), the goal is to generate a glyph image that preserves both the structural correctness of the target character and the stylistic characteristics of the target hand.

Let $\mathcal{S} = \{s_1, s_2, \dots, s_k\}$ denote a small set of reference glyphs in the target style, and let $c$ denote the target character identity. The base generator $G$ produces a glyph image $\hat{y} = G(c, \mathcal{S})$. In the proposed framework, an additional retrieval step provides a set of structurally relevant exemplars $\mathcal{R} = \{r_1, r_2, \dots, r_m\}$ retrieved from an external knowledge base $\mathcal{K}$, so that the augmented generation becomes $\hat{y} = G(c, \mathcal{S}, \mathcal{R})$.

FontDiffuser is chosen as the base model because it combines multi-scale content aggregation with style contrastive learning, so that both complex character structure and large style variation can be handled more robustly [@2024yangfontdiffuser]. Its content encoder and style encoder provide natural injection points for retrieved structural features.

The focus of this work is on rare and complex characters:
- **Rare characters**: characters that appear infrequently or not at all in the training set, determined by character frequency rank in the training corpus.
- **Complex characters**: characters with high stroke counts or dense component layouts, regardless of their frequency.

These two categories overlap but are not identical. The experimental evaluation examines both dimensions.


### Knowledge Base Construction

The retrieval mechanism requires an external knowledge base $\mathcal{K}$ that stores calligraphic glyph exemplars in a retrievable form. The knowledge base is constructed offline before inference and does not change during generation.

The knowledge base is **same-style**: $\mathcal{K}$ contains only glyphs from the same calligrapher or script style as the target. This ensures that all retrieved exemplars share the target hand's stylistic characteristics, avoiding style mismatch between the retrieved references and the generation target. Using a same-style knowledge base also simplifies the retrieval problem, because the retrieval module only needs to find structurally relevant exemplars without simultaneously resolving style compatibility.

Each entry in $\mathcal{K}$ consists of:
- A glyph image in the target calligraphic style
- The character identity (Unicode)
- Structural metadata: component decomposition sequence and structure code, following the Chinese Standard Interchange Code
- A visual feature vector extracted by the image encoder of the base model, computed once at indexing time

The knowledge base is populated from the DeepCalliFont training data [@2024liudeepcallifont]. For each target calligrapher, the glyphs available in that calligrapher's training set form the knowledge base. Although the knowledge base shares its source with the training set, the base model does not have explicit access to specific exemplars at inference time. Retrieval bridges this gap by providing direct visual reference, which is especially valuable when parametric recall is unreliable — a condition empirically observed for rare and complex characters. For unseen characters (zero-shot), the knowledge base does not contain the target character itself, but can still provide structurally similar exemplars (e.g., characters sharing the same spatial configuration or component). This is the scenario where retrieval is expected to be most beneficial.


### Retrieval Module

The retrieval module selects structurally relevant exemplars from $\mathcal{K}$ given a target character $c$. It operates at inference time and is independent of the base generator's training.

#### Retrieval Strategy

The primary retrieval strategy is **whole-glyph retrieval with structural filtering**. Given a target character $c$, the retrieval module:

1. **Structural filtering**: first narrows the candidate set to glyphs that share the same structural configuration type (e.g., left-right, top-bottom, enclosure) as the target character. Chinese characters have a limited number of common spatial configurations [@2025wangdeep; @2025chenadvancements], and characters within the same configuration category share similar spatial layout constraints. This filtering step ensures that retrieved exemplars are structurally relevant rather than merely visually similar.

2. **Visual ranking**: within the filtered candidates, glyphs are ranked by visual feature similarity using the image encoder of the base model. The top-3 most similar exemplars are selected as $\mathcal{R} = \{r_1, r_2, r_3\}$.

This two-stage strategy combines structural relevance (from the filtering step) with visual similarity (from the ranking step). It retrieves whole glyphs rather than sub-character fragments. This design is deliberate: whole-glyph retrieval keeps the retrieval and fusion pipeline simple and avoids the additional complexity of component segmentation and alignment, while still providing structurally informative references through the structural filtering step. The ablation study (Section X) compares this approach against component-level and random retrieval to quantify the contribution of structural filtering.

#### Trigger Mechanism

Retrieval is activated only when the target character is **rare or complex**. Specifically, retrieval is triggered when:
- The target character's stroke count exceeds a threshold (complex), or
- The target character's frequency in the training corpus falls below a threshold (rare).

For common, structurally simple characters, the base model generates without retrieval ($\hat{y} = G(c, \mathcal{S})$), avoiding unnecessary computation and potential noise from retrieved exemplars.

[TODO: 具体的 stroke count 和 frequency 阈值需要根据数据集分布确定]


### Fusion Strategy

Retrieved exemplars are injected into the base generator through **feature concatenation at the image branch**. The visual features of the top-3 retrieved exemplars are extracted by the same image encoder used for indexing, then concatenated with the content features of the target character before being passed to the decoder. This approach requires only a modification to the input dimension of the decoder and does not introduce new architectural components.

Feature concatenation is chosen over alternatives (such as cross-attention or modification of the IFR module) because it minimises changes to the DeepCalliFont codebase, reducing implementation risk while still providing the generator with direct access to visual features from the retrieved exemplars. Whether the model leverages structural information from these features (rather than merely benefiting from visual redundancy) is tested empirically through the random retrieval ablation: if structurally filtered retrieval outperforms random retrieval of same-style exemplars, this provides evidence that the structural filtering step contributes meaningful layout information beyond generic visual similarity.

[TODO: 具体实现时确认 feature concatenation 的插入点——是在 FontDiffuser content encoder 输出之后、decoder 输入之前]


### Inference Protocol

At test time, the generation process proceeds as follows:

1. **Input**: a target character identity $c$ and a set of style reference glyphs $\mathcal{S}$.
2. **Trigger check**: if $c$ is rare (low training frequency) or complex (high stroke count), retrieval is activated.
3. **Retrieval** (if triggered): the retrieval module filters $\mathcal{K}$ by structural configuration, ranks candidates by visual similarity, and returns $\mathcal{R} = \{r_1, r_2, r_3\}$.
4. **Generation**: the base generator produces $\hat{y} = G(c, \mathcal{S}, \mathcal{R})$ with retrieved features concatenated into the image branch. If retrieval is not triggered, $\hat{y} = G(c, \mathcal{S})$ as in the original FontDiffuser.

The retrieval step introduces additional inference overhead. Feature vectors are pre-computed at indexing time, so the online cost consists of nearest-neighbour search over the knowledge base and feature extraction for the top-3 results. The exact overhead is measured empirically in the experiment.

The retrieval mechanism is not intended to replace the base model's generative capability. It provides supplementary structural information where the model's parametric memory is most likely to be insufficient, consistent with the broader RAG paradigm [@2023gaoragsurvey; @2025zhengragvision].


---

## Experiment

### Experimental Setup

#### Dataset

The experiments use the datasets associated with FontDiffuser [@2024yangfontdiffuser]:
- **Training data**: Chinese calligraphy glyph images with corresponding component decomposition sequences and structure codes following the Chinese Standard Interchange Code.
- **Test data**: generation is evaluated on a held-out character set covering common, uncommon, and unseen characters, as well as simple and complex characters by stroke count.

All experiments are conducted on regular script (楷书) only. Regular script has the clearest component boundaries, making structural correctness easier to define and evaluate. Both FontDiffuser and CalliFormer provide strong regular script baselines with existing published results for comparison.

#### Definition of Rare and Complex Characters

Characters in the test set are categorised along two dimensions:

1. **Rarity** (based on character frequency in the training corpus):
   - *Common*: characters appearing in the top 50% by frequency.
   - *Uncommon*: characters appearing in the bottom 50% but still present in training.
   - *Unseen*: characters not present in the training set at all (zero-shot).

2. **Complexity** (based on stroke count):
   - *Simple*: fewer than 10 strokes.
   - *Complex*: 10 strokes or more.

[TODO: 具体阈值根据实际数据集分布调整]

#### Implementation Details

- The base model follows the FontDiffuser architecture and training protocol [@2024yangfontdiffuser], with few-shot fine-tuning on 100 sample characters per target font.
- The knowledge base is indexed offline using pre-computed feature vectors from the image encoder.
- All experiments are conducted on [TODO: GPU 型号和数量].


### Baselines

1. **FontDiffuser** [@2024yangfontdiffuser]: the original model without retrieval augmentation. This is the primary baseline.
2. **FontDiffuser + retrieval** (proposed): the same model augmented with the retrieval mechanism described above (same-style knowledge base, whole-glyph retrieval with structural filtering, feature concatenation, top-3, triggered on rare/complex characters).
3. **CalliFormer** [@2025zhoucalliformer]: a structure-aware Transformer that uses explicit component sequence and structural code as input. This represents an alternative approach to improving structural correctness — stronger structural encoding rather than retrieval augmentation. [TODO: 取决于代码可获取性]


### Evaluation Metrics

**Image quality**:
- **FID** (Fréchet Inception Distance): distributional distance between generated and real glyph images. Lower is better. Used in DeepCalliFont [@2024liudeepcallifont] and Diff-Font [@2024hedifffontb].
- **SSIM** (Structural Similarity Index): pixel-level structural similarity to ground truth. Higher is better. Used in CalliFormer [@2025zhoucalliformer] and Diff-Font [@2024hedifffontb].
- **LPIPS** (Learned Perceptual Image Patch Similarity): perceptual distance using deep features. Lower is better. Used in DeepCalliFont [@2024liudeepcallifont] and Liu et al. [@2025liuchinese].

**Structural correctness**:
- **Content recognition accuracy**: a pre-trained Chinese character recogniser is applied to the generated images. Recognition accuracy serves as a proxy for structural correctness. Used in Liu et al. [@2025liuchinese] and Diff-Font [@2024hedifffontb] (reported as ACCC).

**Qualitative evaluation**:
- Visual comparison of generated glyphs, focusing on rare and complex characters.
- Error categorisation: missing strokes, extra strokes, component misplacement, stroke connectivity errors, glyph collapse [@2024hedifffontb; @2025liuchinese].


### Results and Analysis

#### Main Comparison

[TODO: 实验结果]

| Method | FID ↓ | SSIM ↑ | LPIPS ↓ | Content Acc. ↑ |
|--------|-------|--------|---------|----------------|
| FontDiffuser | — | — | — | — |
| FontDiffuser + retrieval | — | — | — | — |
| CalliFormer | — | — | — | — |

#### Performance by Character Category

[TODO: 实验结果]

| Character Group | Baseline Content Acc. | Proposed Content Acc. | Baseline FID | Proposed FID |
|-----------------|----------------------|----------------------|-------------|-------------|
| Common + Simple | — | — | — | — |
| Common + Complex | — | — | — | — |
| Uncommon + Simple | — | — | — | — |
| Uncommon + Complex | — | — | — | — |
| Unseen + Simple | — | — | — | — |
| Unseen + Complex | — | — | — | — |

#### Qualitative Examples

[TODO: 可视化对比，包括：
1. rare + complex 字（预期 retrieval 帮助最大）
2. common + simple 字（预期帮助较小）
3. failure case（如果存在）]

#### Failure Case Analysis

[TODO: 实验后分析。关注：
1. 知识库中结构相关但布局不同的 exemplar 是否误导生成
2. 极端 rare 的字在知识库中无足够相关 exemplar 的情况]


### Ablation Study

All ablations use the same dataset and evaluation metrics as the main experiment. Each ablation changes one variable while keeping all others at the default setting (whole-glyph retrieval with structural filtering, feature concatenation, top-3, rare/complex trigger).

#### Retrieval Strategy

Compares the primary whole-glyph retrieval with structural filtering against three alternatives:
- **Random retrieval**: retrieves 3 random glyphs from the same-style knowledge base, without any structural filtering. This baseline tests whether the improvement comes from structural relevance or merely from additional visual features of the same style.
- **Component-level retrieval**: retrieves glyphs sharing components (radicals) with the target character, using component decomposition from the Chinese Standard Interchange Code [@2020wucalligan].
- **Structurally similar retrieval (no visual ranking)**: retrieves characters with the same structural configuration type, selected randomly within the filtered set rather than ranked by visual similarity. This isolates the contribution of structural filtering from visual ranking.

[TODO: 实验结果]

#### Top-$k$

Varies $k$ = 1, 3, 5, 10 to examine the trade-off between coverage and noise.

[TODO: 实验结果]

#### Trigger: Always-On vs. Selective

Compares the default rare/complex trigger against always-on retrieval (applied to every character regardless of rarity or complexity).

[TODO: 实验结果]

#### Computational Overhead

Reports retrieval time per character and total inference time compared to the baseline.

[TODO: 实验测量]



